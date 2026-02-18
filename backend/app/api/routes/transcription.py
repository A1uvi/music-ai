from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional, List

from ...models.requests import TranscribeUrlRequest
from ...models.responses import (
    TranscribeResponse,
    TranscriptionJobResult,
    JobStatus,
    NoteData,
    TranscriptionResult
)
from ...services.audio_extractor import AudioExtractor
from ...services.pitch_detector import PitchDetector
from ...services.note_quantizer import NoteQuantizer
from ...services.notation_generator import NotationGenerator
from ...services.audio_preprocessor import AudioPreprocessor
from ...services.source_separator import SourceSeparator
from ...utils.progress_tracker import progress_tracker
from ...core.exceptions import AudioExtractionError, PitchDetectionError
from ...config import settings

router = APIRouter()

# Initialize services
audio_extractor = AudioExtractor(settings.temp_dir)
pitch_detector = PitchDetector(
    sample_rate=settings.sample_rate,
    hop_length=settings.hop_length
)


@router.post("/transcribe/url", response_model=TranscribeResponse)
async def transcribe_from_url(request: TranscribeUrlRequest):
    """
    Initiate transcription from a URL.

    Returns:
        Job ID and SSE endpoint for progress tracking
    """
    job_id = str(uuid.uuid4())
    progress_tracker.create_job(job_id)

    asyncio.create_task(
        process_transcription_url(
            job_id,
            request.url,
            allowed_notes=request.allowed_notes,
            enable_source_separation=request.enable_source_separation,
        )
    )

    return TranscribeResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        sse_endpoint=f"/api/py/transcribe/status/{job_id}"
    )


@router.post("/transcribe/upload", response_model=TranscribeResponse)
async def transcribe_from_upload(
    file: UploadFile = File(...),
    allowed_notes: Optional[str] = Form(default=None),
    enable_source_separation: bool = Form(default=False),
):
    """
    Initiate transcription from uploaded audio file.

    Returns:
        Job ID and SSE endpoint for progress tracking
    """
    contents = await file.read()
    if len(contents) > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
        )

    allowed_types = {
        'audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-wav',
        'video/mp4', 'video/quicktime'
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {allowed_types}"
        )

    # Parse JSON-encoded allowed_notes string from FormData
    parsed_notes: Optional[List[str]] = None
    if allowed_notes:
        try:
            parsed_notes = json.loads(allowed_notes)
        except (json.JSONDecodeError, TypeError):
            parsed_notes = None

    job_id = str(uuid.uuid4())
    file_path = settings.temp_dir / f"{job_id}_upload{Path(file.filename).suffix}"
    with open(file_path, 'wb') as f:
        f.write(contents)

    progress_tracker.create_job(job_id)

    asyncio.create_task(
        process_transcription_file(
            job_id,
            file_path,
            allowed_notes=parsed_notes,
            enable_source_separation=enable_source_separation,
        )
    )

    return TranscribeResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        sse_endpoint=f"/api/py/transcribe/status/{job_id}"
    )


@router.get("/transcribe/status/{job_id}")
async def get_transcription_status(job_id: str):
    """
    SSE endpoint for real-time progress updates.

    Returns:
        Server-sent events stream
    """
    async def event_generator():
        queue = progress_tracker.subscribe(job_id)

        try:
            while True:
                try:
                    event_type, data = await asyncio.wait_for(
                        queue.get(),
                        timeout=30.0
                    )

                    if event_type == 'progress':
                        yield f"event: progress\n"
                        yield f"data: {data.model_dump_json()}\n\n"
                    elif event_type == 'complete':
                        yield f"event: complete\n"
                        yield f"data: {json.dumps(data)}\n\n"
                        break
                    elif event_type == 'error':
                        yield f"event: error\n"
                        yield f"data: {json.dumps(data)}\n\n"
                        break

                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"

        finally:
            progress_tracker.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/transcribe/result/{job_id}", response_model=TranscriptionJobResult)
async def get_transcription_result(job_id: str):
    """
    Retrieve completed transcription result.

    Returns:
        Complete transcription result with VexFlow data
    """
    job_status = progress_tracker.get_job_status(job_id)

    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_status['status'] == JobStatus.FAILED:
        return TranscriptionJobResult(
            job_id=job_id,
            status=JobStatus.FAILED,
            error=job_status.get('error', 'Unknown error')
        )

    if job_status['status'] != JobStatus.COMPLETED:
        return TranscriptionJobResult(
            job_id=job_id,
            status=job_status['status']
        )

    result_data = job_status.get('result')
    if not result_data:
        raise HTTPException(status_code=500, detail="Result data missing")

    return TranscriptionJobResult(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        result=result_data['result'],
        vexflow_data=result_data['vexflow_data']
    )


async def process_transcription_url(
    job_id: str,
    url: str,
    allowed_notes: Optional[List[str]] = None,
    enable_source_separation: bool = False,
):
    """Background task to process transcription from URL."""
    try:
        await progress_tracker.update_progress(
            job_id,
            JobStatus.DOWNLOADING,
            10,
            "Extracting audio from URL"
        )

        audio_path = await audio_extractor.extract_from_url(url, job_id)
        await process_audio_file(
            job_id,
            audio_path,
            allowed_notes=allowed_notes,
            enable_source_separation=enable_source_separation,
        )

    except AudioExtractionError as e:
        await progress_tracker.fail_job(job_id, f"Audio extraction failed: {str(e)}")
    except Exception as e:
        await progress_tracker.fail_job(job_id, f"Processing failed: {str(e)}")
    finally:
        cleanup_audio_files(job_id)


async def process_transcription_file(
    job_id: str,
    file_path: Path,
    allowed_notes: Optional[List[str]] = None,
    enable_source_separation: bool = False,
):
    """Background task to process transcription from uploaded file."""
    try:
        await process_audio_file(
            job_id,
            file_path,
            allowed_notes=allowed_notes,
            enable_source_separation=enable_source_separation,
        )
    except Exception as e:
        await progress_tracker.fail_job(job_id, f"Processing failed: {str(e)}")
    finally:
        cleanup_audio_files(job_id)


async def process_audio_file(
    job_id: str,
    audio_path: Path,
    allowed_notes: Optional[List[str]] = None,
    enable_source_separation: bool = False,
):
    """Common audio processing pipeline."""
    loop = asyncio.get_running_loop()
    temp_files: List[Path] = []  # preprocessing temp files to clean up

    try:
        detection_path = audio_path

        # Phase 2b: melody source separation (opt-in — slow on CPU)
        if enable_source_separation:
            await progress_tracker.update_progress(
                job_id,
                JobStatus.SEPARATING,
                20,
                "Separating melody from accompaniment"
            )
            sep_path = await loop.run_in_executor(
                None,
                lambda: SourceSeparator.separate_melody(detection_path),
            )
            if sep_path != detection_path:
                temp_files.append(sep_path)
                detection_path = sep_path

        # Phase 2a: stationary noise reduction (enabled by default when available)
        if settings.enable_preprocessing:
            denoised_path = await loop.run_in_executor(
                None,
                lambda: AudioPreprocessor.preprocess(detection_path, settings.sample_rate),
            )
            if denoised_path != detection_path:
                temp_files.append(denoised_path)
                detection_path = denoised_path

        await progress_tracker.update_progress(
            job_id,
            JobStatus.ANALYZING,
            30,
            "Detecting pitches from audio"
        )

        # Phase 3b: detect_pitches now returns (events, tempo, time_signature)
        pitch_events, detected_tempo, time_signature = await pitch_detector.detect_pitches(
            detection_path
        )

        if not pitch_events:
            raise PitchDetectionError("No pitches detected in audio")

        await progress_tracker.update_progress(
            job_id,
            JobStatus.QUANTIZING,
            60,
            "Extracting melody notes"
        )

        # Phase 1c + 3a: allowed_notes wired; Viterbi DP quantization
        quantizer = NoteQuantizer(
            allowed_notes=allowed_notes,
            tempo=detected_tempo,
            time_signature=time_signature,
        )
        musical_notes = await quantizer.quantize_pitches(pitch_events)

        await progress_tracker.update_progress(
            job_id,
            JobStatus.GENERATING,
            80,
            "Generating sheet music notation"
        )

        # Phase 3b: pass detected time_signature to notation generator
        notation_gen = NotationGenerator(time_signature=time_signature)
        vexflow_data, metadata = await notation_gen.generate_vexflow_data(
            musical_notes, tempo=int(round(detected_tempo))
        )

        note_data_list = [
            NoteData(
                pitch=note.pitch,
                octave=note.octave,
                duration=note.duration,
                start_time=note.start_time,
                original_frequency=note.original_frequency,
                quantized_note=note.quantized_note
            )
            for note in musical_notes
        ]

        result = TranscriptionResult(
            notes=note_data_list,
            metadata=metadata
        )

        await progress_tracker.complete_job(
            job_id,
            {
                'result': result.model_dump(),
                'vexflow_data': vexflow_data.model_dump()
            }
        )

    finally:
        # Clean up preprocessing temp files
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass


def cleanup_audio_files(job_id: str):
    """Clean up temporary audio files."""
    for pattern in [f"{job_id}.*", f"{job_id}_upload.*"]:
        for file in settings.temp_dir.glob(pattern):
            try:
                file.unlink()
            except Exception:
                pass
