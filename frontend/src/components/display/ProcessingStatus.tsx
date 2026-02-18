'use client'

import { useEffect, useRef } from 'react'
import { ProgressBar } from '@/components/ui/ProgressBar'
import type { LogEntry } from '@/hooks/useTranscription'

interface ProcessingStatusProps {
  stage: string
  progress: number
  logs: LogEntry[]
}

const PIPELINE_STAGES = [
  { key: 'queued',       label: 'Queued' },
  { key: 'downloading',  label: 'Download' },
  { key: 'preprocessing',label: 'Preprocess' },
  { key: 'analyzing',    label: 'Analyze' },
  { key: 'quantizing',   label: 'Quantize' },
  { key: 'generating',   label: 'Generate' },
  { key: 'completed',    label: 'Done' },
]

function getStageIndex(stage: string): number {
  const idx = PIPELINE_STAGES.findIndex(s => s.key === stage)
  return idx === -1 ? 0 : idx
}

const LOG_COLORS: Record<LogEntry['type'], string> = {
  system:  'text-blue-400',
  info:    'text-gray-300',
  success: 'text-emerald-400',
  error:   'text-red-400',
}

const LOG_PREFIXES: Record<LogEntry['type'], string> = {
  system:  '→',
  info:    '·',
  success: '✓',
  error:   '✗',
}

export function ProcessingStatus({ stage, progress, logs }: ProcessingStatusProps) {
  const terminalRef = useRef<HTMLDivElement>(null)
  const activeIndex = getStageIndex(stage)
  const isFailed = stage === 'failed'

  // Auto-scroll terminal to bottom on new logs
  useEffect(() => {
    const el = terminalRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [logs])

  return (
    <div className="space-y-6">
      {/* Stage pipeline */}
      <div>
        <div className="flex items-center gap-0 overflow-x-auto pb-1">
          {PIPELINE_STAGES.map((s, idx) => {
            const isActive = !isFailed && idx === activeIndex
            const isDone   = !isFailed && idx < activeIndex
            const isFail   = isFailed && idx === activeIndex

            return (
              <div key={s.key} className="flex items-center flex-shrink-0">
                {/* Step */}
                <div className="flex flex-col items-center gap-1">
                  <div
                    className={[
                      'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-300',
                      isActive
                        ? 'bg-primary text-white ring-2 ring-primary ring-offset-2'
                        : isDone
                        ? 'bg-success text-white'
                        : isFail
                        ? 'bg-error text-white'
                        : 'bg-border text-text-secondary',
                    ].join(' ')}
                  >
                    {isDone ? (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    ) : isFail ? (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    ) : (
                      <span>{idx + 1}</span>
                    )}
                  </div>
                  <span
                    className={[
                      'text-xs whitespace-nowrap',
                      isActive ? 'text-primary font-medium' : isDone ? 'text-success' : 'text-text-secondary',
                    ].join(' ')}
                  >
                    {s.label}
                  </span>
                </div>

                {/* Connector line */}
                {idx < PIPELINE_STAGES.length - 1 && (
                  <div
                    className={[
                      'h-px w-8 mx-1 mb-4 transition-colors duration-300 flex-shrink-0',
                      idx < activeIndex ? 'bg-success' : 'bg-border',
                    ].join(' ')}
                  />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-text">
            {isFailed ? 'Failed' : stage === 'completed' ? 'Complete' : 'Processing'}
          </span>
          <span className="text-sm tabular-nums text-text-secondary">{progress}%</span>
        </div>
        <ProgressBar value={progress} label="Progress" />
      </div>

      {/* Terminal output */}
      <div>
        {/* Terminal header */}
        <div
          className="flex items-center gap-2 px-4 py-2 rounded-t-lg"
          style={{ background: '#1a1a1a' }}
        >
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ background: '#FF5F57' }} />
            <span className="w-3 h-3 rounded-full" style={{ background: '#FEBC2E' }} />
            <span className="w-3 h-3 rounded-full" style={{ background: '#28C840' }} />
          </div>
          <span className="text-xs font-medium ml-2" style={{ color: '#888', fontFamily: 'ui-monospace, monospace' }}>
            job output
          </span>
          {!isFailed && stage !== 'completed' && (
            <span className="ml-auto flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-live-pulse" />
              <span className="text-xs" style={{ color: '#888', fontFamily: 'ui-monospace, monospace' }}>live</span>
            </span>
          )}
        </div>

        {/* Terminal body */}
        <div
          ref={terminalRef}
          className="rounded-b-lg overflow-y-auto"
          style={{
            background: '#0d0d0d',
            height: '220px',
            fontFamily: 'ui-monospace, "Cascadia Code", "Fira Code", monospace',
            fontSize: '13px',
            lineHeight: '1.6',
            padding: '12px 16px',
          }}
        >
          {logs.length === 0 ? (
            <span style={{ color: '#444' }}>Waiting for job to start...</span>
          ) : (
            logs.map((entry) => (
              <div key={entry.id} className="flex gap-2">
                <span style={{ color: '#555', flexShrink: 0 }}>[{entry.timestamp}]</span>
                <span className={`${LOG_COLORS[entry.type]} flex-shrink-0`}>
                  {LOG_PREFIXES[entry.type]}
                </span>
                <span className={LOG_COLORS[entry.type]}>{entry.message}</span>
              </div>
            ))
          )}
          {/* Blinking cursor when active */}
          {!isFailed && stage !== 'completed' && logs.length > 0 && (
            <div className="flex gap-2 mt-0.5">
              <span style={{ color: '#555', flexShrink: 0, whiteSpace: 'pre' }}>{'           '}</span>
              <span className="text-gray-400 animate-terminal-blink">▌</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
