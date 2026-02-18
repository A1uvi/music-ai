import asyncio
from typing import Dict, Set, Optional
from ..models.responses import ProgressEvent, JobStatus


class ProgressTracker:
    """
    Tracks progress for transcription jobs and broadcasts updates via SSE.
    """

    def __init__(self):
        """Initialize progress tracker."""
        self._jobs: Dict[str, Dict] = {}
        self._queues: Dict[str, Set[asyncio.Queue]] = {}

    def create_job(self, job_id: str) -> None:
        """
        Create a new job for tracking.

        Args:
            job_id: Unique job identifier
        """
        self._jobs[job_id] = {
            'status': JobStatus.QUEUED,
            'progress': 0,
            'message': 'Job queued',
            'result': None,
            'error': None
        }
        self._queues[job_id] = set()

    def subscribe(self, job_id: str) -> asyncio.Queue:
        """
        Subscribe to progress updates for a job.

        Args:
            job_id: Job identifier

        Returns:
            Queue that will receive progress events
        """
        if job_id not in self._queues:
            self._queues[job_id] = set()

        queue = asyncio.Queue()
        self._queues[job_id].add(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        """
        Unsubscribe from job updates.

        Args:
            job_id: Job identifier
            queue: Queue to remove
        """
        if job_id in self._queues:
            self._queues[job_id].discard(queue)

    async def update_progress(
        self,
        job_id: str,
        status: JobStatus,
        percent: int,
        message: str
    ) -> None:
        """
        Update job progress and notify subscribers.

        Args:
            job_id: Job identifier
            status: Current status
            percent: Progress percentage (0-100)
            message: Human-readable message
        """
        if job_id not in self._jobs:
            return

        self._jobs[job_id].update({
            'status': status,
            'progress': percent,
            'message': message
        })

        event = ProgressEvent(
            stage=status.value,
            percent=percent,
            message=message
        )

        # Broadcast to all subscribers
        if job_id in self._queues:
            for queue in self._queues[job_id]:
                try:
                    await queue.put(('progress', event))
                except Exception:
                    pass

    async def complete_job(self, job_id: str, result: Dict) -> None:
        """
        Mark job as completed with result.

        Args:
            job_id: Job identifier
            result: Transcription result data
        """
        if job_id not in self._jobs:
            return

        self._jobs[job_id].update({
            'status': JobStatus.COMPLETED,
            'progress': 100,
            'message': 'Transcription completed',
            'result': result
        })

        # Notify subscribers
        if job_id in self._queues:
            for queue in self._queues[job_id]:
                try:
                    await queue.put(('complete', result))
                except Exception:
                    pass

    async def fail_job(self, job_id: str, error: str) -> None:
        """
        Mark job as failed with error.

        Args:
            job_id: Job identifier
            error: Error message
        """
        if job_id not in self._jobs:
            return

        self._jobs[job_id].update({
            'status': JobStatus.FAILED,
            'message': f'Failed: {error}',
            'error': error
        })

        # Notify subscribers
        if job_id in self._queues:
            for queue in self._queues[job_id]:
                try:
                    await queue.put(('error', {'error': error}))
                except Exception:
                    pass

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get current job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status dict or None if not found
        """
        return self._jobs.get(job_id)

    def cleanup_job(self, job_id: str) -> None:
        """
        Remove job from tracking (call after result retrieval).

        Args:
            job_id: Job identifier
        """
        self._jobs.pop(job_id, None)
        self._queues.pop(job_id, None)


# Global progress tracker instance
progress_tracker = ProgressTracker()
