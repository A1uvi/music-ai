'use client'

import { useState, useCallback, useRef } from 'react'
import { apiClient } from '@/lib/api-client'
import { useSSE } from './useSSE'
import type { TranscriptionResult, VexFlowData } from '@/types/api'

export interface LogEntry {
  id: string
  timestamp: string
  message: string
  type: 'system' | 'info' | 'success' | 'error'
}

function makeTimestamp(): string {
  return new Date().toTimeString().slice(0, 8)
}

const STAGE_FALLBACK_MESSAGES: Record<string, string> = {
  queued:        'Job queued — waiting for worker...',
  downloading:   'Extracting audio from source...',
  separating:    'Separating melody from accompaniment...',
  preprocessing: 'Converting audio format...',
  analyzing:     'Running pitch detection (this may take a while)...',
  quantizing:    'Extracting melody notes...',
  generating:    'Generating sheet music notation...',
  completed:     'All stages complete.',
}

export function useTranscription() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState<string>('idle')
  const [result, setResult] = useState<TranscriptionResult | null>(null)
  const [vexflowData, setVexflowData] = useState<VexFlowData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const logCounterRef = useRef(0)
  const lastLoggedStageRef = useRef<string>('')

  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    logCounterRef.current += 1
    const entry: LogEntry = {
      id: `${logCounterRef.current}`,
      timestamp: makeTimestamp(),
      message,
      type,
    }
    setLogs(prev => [...prev, entry])
  }, [])

  const { connect, disconnect } = useSSE({
    onProgress: (data) => {
      setProgress(data.percent)
      setStage(data.stage)
      if (data.stage !== lastLoggedStageRef.current) {
        lastLoggedStageRef.current = data.stage
        const msg = data.message || STAGE_FALLBACK_MESSAGES[data.stage] || `Stage: ${data.stage}`
        addLog(msg, 'info')
      }
    },
    onComplete: (data) => {
      setResult(data.result)
      setVexflowData(data.vexflow_data)
      setProgress(100)
      setStage('completed')
      setIsProcessing(false)
      addLog('Transcription completed successfully.', 'success')
    },
    onError: (err) => {
      setError(err.error)
      setStage('failed')
      setIsProcessing(false)
      addLog(`Error: ${err.error}`, 'error')
    },
  })

  const submitUrl = useCallback(async (
    url: string,
    allowedNotes?: string[],
    separateMelody?: boolean,
  ) => {
    logCounterRef.current = 0
    lastLoggedStageRef.current = ''
    setLogs([{
      id: '0',
      timestamp: makeTimestamp(),
      message: 'Job submitted. Connecting to processing queue...',
      type: 'system',
    }])

    try {
      setError(null)
      setIsProcessing(true)
      setProgress(0)
      setStage('queued')

      const response = await apiClient.transcribeFromUrl({
        url,
        source_type: 'youtube',
        allowed_notes: allowedNotes,
        enable_source_separation: separateMelody ?? false,
      })

      setJobId(response.job_id)
      addLog(`Job ID: ${response.job_id}`, 'system')
      addLog('Awaiting worker assignment...', 'system')
      connect(response.sse_endpoint)
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to start transcription'
      setError(msg)
      setIsProcessing(false)
      addLog(`Failed to submit: ${msg}`, 'error')
    }
  }, [connect, addLog])

  const submitFile = useCallback(async (
    file: File,
    allowedNotes?: string[],
    separateMelody?: boolean,
  ) => {
    logCounterRef.current = 0
    lastLoggedStageRef.current = ''
    setLogs([{
      id: '0',
      timestamp: makeTimestamp(),
      message: `Uploading file: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`,
      type: 'system',
    }])

    try {
      setError(null)
      setIsProcessing(true)
      setProgress(0)
      setStage('queued')

      const response = await apiClient.transcribeFromUpload(file, allowedNotes, separateMelody)

      setJobId(response.job_id)
      addLog(`Job ID: ${response.job_id}`, 'system')
      addLog('Awaiting worker assignment...', 'system')
      connect(response.sse_endpoint)
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to start transcription'
      setError(msg)
      setIsProcessing(false)
      addLog(`Failed to submit: ${msg}`, 'error')
    }
  }, [connect, addLog])

  const reset = useCallback(() => {
    disconnect()
    setJobId(null)
    setProgress(0)
    setStage('idle')
    setResult(null)
    setVexflowData(null)
    setError(null)
    setIsProcessing(false)
    setLogs([])
  }, [disconnect])

  return {
    jobId,
    progress,
    stage,
    result,
    vexflowData,
    error,
    isProcessing,
    logs,
    submitUrl,
    submitFile,
    reset,
  }
}
