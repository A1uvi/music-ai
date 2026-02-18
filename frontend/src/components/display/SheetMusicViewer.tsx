'use client'

import { useEffect, useRef } from 'react'
import type { VexFlowData, MusicMetadata, NoteData } from '@/types/api'
import { useAudioPlayback } from '@/hooks/useAudioPlayback'

interface SheetMusicViewerProps {
  vexflowData: VexFlowData
  metadata: MusicMetadata
  notes: NoteData[]
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// VexFlow requires enharmonic flat spellings for certain keys.
const ENHARMONIC_KEYS: Record<string, string> = {
  'C#': 'Db', 'D#': 'Eb', 'G#': 'Ab', 'A#': 'Bb',
}

export function SheetMusicViewer({
  vexflowData,
  metadata,
  notes,
}: SheetMusicViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const { play, pause, stop, playbackState, currentTime, totalDuration } =
    useAudioPlayback(notes, metadata)

  const isPlaying = playbackState === 'playing'
  const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0

  const handlePlayPause = () => {
    if (isPlaying) pause()
    else void play()
  }

  useEffect(() => {
    if (!containerRef.current || typeof window === 'undefined') return

    const container = containerRef.current

    const render = () => {
      // Dynamically import VexFlow only on client side.
      // next.config.js aliases 'vexflow' to the CJS build. Webpack wraps CJS
      // module.exports under `.default` in ESM interop — unwrap before destructuring.
      import('vexflow').then((vfRaw) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const { Renderer, Stave, StaveNote, Voice, Formatter } = ((vfRaw as any).default ?? vfRaw) as typeof import('vexflow')
        if (!containerRef.current) return

        container.innerHTML = ''

        const validMeasures = vexflowData.measures.filter((m) => m.notes.length > 0)
        if (validMeasures.length === 0) return

        const safeKey = ENHARMONIC_KEYS[vexflowData.key] ?? vexflowData.key

        // Layout constants
        const containerWidth = container.clientWidth || 800
        const MARGIN = 8
        const STAVE_GAP = 6          // horizontal gap between staves
        const ROW_HEIGHT = 120       // px per row (stave height + vertical breathing room)
        const Y_STAVE_TOP = 32       // y offset to first stave line within each row
        const TARGET_STAVE_WIDTH = 200

        const usableWidth = containerWidth - MARGIN * 2
        const measuresPerRow = Math.max(
          1,
          Math.floor((usableWidth + STAVE_GAP) / (TARGET_STAVE_WIDTH + STAVE_GAP))
        )
        // Fill the row evenly — each stave gets an equal share of usable width
        const staveWidth = Math.floor((usableWidth - (measuresPerRow - 1) * STAVE_GAP) / measuresPerRow)

        const numRows = Math.ceil(validMeasures.length / measuresPerRow)
        const totalHeight = numRows * ROW_HEIGHT + Y_STAVE_TOP

        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const svgBackend: number = (Renderer as any)?.Backends?.SVG ?? 2
          const renderer = new Renderer(container, svgBackend)
          renderer.resize(containerWidth, totalHeight)
          const context = renderer.getContext()

          validMeasures.forEach((measure, index) => {
            const rowIndex = Math.floor(index / measuresPerRow)
            const colIndex = index % measuresPerRow
            const isFirstInRow = colIndex === 0
            const isVeryFirst = index === 0

            const x = MARGIN + colIndex * (staveWidth + STAVE_GAP)
            const y = rowIndex * ROW_HEIGHT + Y_STAVE_TOP

            const stave = new Stave(x, y, staveWidth)

            // Clef at the start of every row (standard notation practice).
            // Key signature and time signature only on the very first stave.
            if (isFirstInRow) {
              stave.addClef(vexflowData.clef)
            }
            if (isVeryFirst) {
              stave.addKeySignature(safeKey)
              stave.addTimeSignature(metadata.time_signature)
            }

            stave.setContext(context).draw()

            const staveNotes = measure.notes.map((noteData) =>
              new StaveNote({ keys: noteData.keys, duration: noteData.duration })
            )

            // SOFT mode: allows partial measures (pickup bars, trailing measures)
            // without throwing a strict beat-count validation error.
            const voice = new Voice({ numBeats: 4, beatValue: 4 }).setMode(Voice.Mode.SOFT)
            voice.addTickables(staveNotes)

            // Subtract clef/sig overhead from formatter width so notes don't
            // overflow the stave boundary.
            const overhead = isVeryFirst ? 80 : isFirstInRow ? 28 : 8
            new Formatter().joinVoices([voice]).format([voice], staveWidth - overhead)

            voice.draw(context, stave)
          })
        } catch (error) {
          console.error('VexFlow rendering error:', error)
          container.innerHTML = '<p style="padding:16px;color:var(--color-error,#dc2626)">Error rendering sheet music</p>'
        }
      })
    }

    render()

    // Re-render when the container is resized (e.g. window resize, sidebar toggle)
    const ro = new ResizeObserver(() => render())
    ro.observe(container)
    return () => ro.disconnect()
  }, [vexflowData, metadata])

  return (
    <div className="space-y-4">
      {/* Header row */}
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold text-text">Sheet Music</h3>
        <div className="text-sm text-text-secondary space-x-4">
          <span>Key: {metadata.key_signature}</span>
          <span>Tempo: {metadata.tempo} BPM</span>
          <span>Notes: {metadata.note_count}</span>
        </div>
      </div>

      {/* Playback controls */}
      <div className="flex items-center gap-3 py-3 border-t border-b border-border">
        {/* Play / Pause */}
        <button
          onClick={handlePlayPause}
          className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full bg-primary text-white hover:bg-primary-hover transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden>
              <rect x="1.5" y="1" width="3.5" height="11" rx="1" fill="currentColor" />
              <rect x="8" y="1" width="3.5" height="11" rx="1" fill="currentColor" />
            </svg>
          ) : (
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden>
              <path d="M2.5 1.5L11.5 6.5L2.5 11.5V1.5Z" fill="currentColor" />
            </svg>
          )}
        </button>

        {/* Stop — only visible when not idle */}
        {playbackState !== 'idle' && (
          <button
            onClick={stop}
            className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded text-text-secondary hover:text-text hover:bg-border transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
            aria-label="Stop"
          >
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none" aria-hidden>
              <rect x="1" y="1" width="9" height="9" rx="1.5" fill="currentColor" />
            </svg>
          </button>
        )}

        {/* Progress bar */}
        <div className="flex-1 h-1 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full"
            style={{ width: `${progress}%`, transition: 'none' }}
          />
        </div>

        {/* Time */}
        <span className="flex-shrink-0 text-xs text-text-secondary font-mono tabular-nums w-20 text-right">
          {formatTime(currentTime)} / {formatTime(totalDuration)}
        </span>
      </div>

      {/* Sheet music canvas — height grows to fit all measures */}
      <div
        ref={containerRef}
        className="border border-border rounded p-0 bg-bg overflow-x-hidden"
      />
    </div>
  )
}
