import axios from 'axios'
import type {
  TranscribeUrlRequest,
  TranscribeResponse,
  TranscriptionJobResult,
} from '@/types/api'

const API_BASE = '/api/py'

export const apiClient = {
  async transcribeFromUrl(request: TranscribeUrlRequest): Promise<TranscribeResponse> {
    const response = await axios.post(`${API_BASE}/transcribe/url`, request)
    return response.data
  },

  async transcribeFromUpload(
    file: File,
    allowedNotes?: string[],
    separateMelody?: boolean,
  ): Promise<TranscribeResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (allowedNotes !== undefined) {
      formData.append('allowed_notes', JSON.stringify(allowedNotes))
    }
    if (separateMelody !== undefined) {
      formData.append('enable_source_separation', String(separateMelody))
    }

    const response = await axios.post(`${API_BASE}/transcribe/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async getResult(jobId: string): Promise<TranscriptionJobResult> {
    const response = await axios.get(`${API_BASE}/transcribe/result/${jobId}`)
    return response.data
  },

  async checkHealth(): Promise<{ status: string }> {
    const response = await axios.get(`${API_BASE}/health`)
    return response.data
  },
}
