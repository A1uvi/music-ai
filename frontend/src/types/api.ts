export interface TranscribeUrlRequest {
  url: string
  source_type?: 'youtube' | 'youtube_music'
  allowed_notes?: string[]
  enable_source_separation?: boolean
}

export interface TranscribeResponse {
  job_id: string
  status: string
  sse_endpoint: string
}

export interface NoteData {
  pitch: string
  octave: number
  duration: string
  start_time: number
  original_frequency?: number
  quantized_note?: string
}

export interface MusicMetadata {
  tempo: number
  time_signature: string
  key_signature: string
  total_duration: number
  note_count: number
}

export interface TranscriptionResult {
  notes: NoteData[]
  metadata: MusicMetadata
}

export interface VexFlowMeasure {
  notes: Array<{
    keys: string[]
    duration: string
  }>
  time_signature?: string
}

export interface VexFlowData {
  measures: VexFlowMeasure[]
  clef: string
  key: string
}

export interface TranscriptionJobResult {
  job_id: string
  status: string
  result?: TranscriptionResult
  vexflow_data?: VexFlowData
  error?: string
}

export interface ProgressEvent {
  stage: string
  percent: number
  message: string
}
