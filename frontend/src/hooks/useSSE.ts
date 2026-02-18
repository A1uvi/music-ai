'use client'

import { useCallback, useRef } from 'react'
import type { ProgressEvent } from '@/types/api'

interface UseSSEOptions {
  onProgress?: (data: ProgressEvent) => void
  onComplete?: (data: any) => void
  onError?: (error: { error: string }) => void
}

export function useSSE({ onProgress, onComplete, onError }: UseSSEOptions) {
  const eventSourceRef = useRef<EventSource | null>(null)

  const connect = useCallback((endpoint: string) => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    // Create new EventSource
    const eventSource = new EventSource(endpoint)
    eventSourceRef.current = eventSource

    // Handle progress events
    eventSource.addEventListener('progress', (event) => {
      try {
        const data = JSON.parse(event.data) as ProgressEvent
        onProgress?.(data)
      } catch (err) {
        console.error('Failed to parse progress event:', err)
      }
    })

    // Handle complete events
    eventSource.addEventListener('complete', (event) => {
      try {
        const data = JSON.parse(event.data)
        onComplete?.(data)
        eventSource.close()
      } catch (err) {
        console.error('Failed to parse complete event:', err)
      }
    })

    // Handle error events
    eventSource.addEventListener('error', (event: any) => {
      try {
        if (event.data) {
          const data = JSON.parse(event.data)
          onError?.(data)
        } else {
          onError?.({ error: 'Connection error' })
        }
      } catch (err) {
        onError?.({ error: 'Unknown error occurred' })
      }
      eventSource.close()
    })

    // Handle connection errors
    eventSource.onerror = () => {
      onError?.({ error: 'Connection lost. Please check your internet connection.' })
      eventSource.close()
    }

    return eventSource
  }, [onProgress, onComplete, onError])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }, [])

  return { connect, disconnect }
}
