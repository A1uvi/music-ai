'use client'

import { useState } from 'react'
import { MUSICAL_NOTES, SCALE_GROUPS } from '@/lib/constants'
import clsx from 'clsx'

interface NoteSelectionInputProps {
  value: string[]
  onChange: (notes: string[]) => void
}

export function NoteSelectionInput({ value, onChange }: NoteSelectionInputProps) {
  const [activeScale, setActiveScale] = useState<string | null>(null)

  const toggleNote = (note: string) => {
    if (value.includes(note)) {
      onChange(value.filter((n) => n !== note))
    } else {
      onChange([...value, note])
    }
  }

  const selectScale = (scaleName: string, scaleNotes: readonly string[]) => {
    onChange([...scaleNotes])
    setActiveScale(scaleName)
  }

  const selectAll = () => {
    onChange([...MUSICAL_NOTES])
    setActiveScale(null)
  }

  const clearAll = () => {
    onChange([])
    setActiveScale(null)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-text mb-1">
          Allowed Notes
        </label>
        <p className="text-sm text-text-secondary">
          Select which notes can appear in the transcription
        </p>
      </div>

      {/* Scale groups */}
      {Object.entries(SCALE_GROUPS).map(([groupName, scales]) => (
        <div key={groupName}>
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2">
            {groupName}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(scales).map(([scaleName, scaleNotes]) => (
              <button
                key={scaleName}
                type="button"
                onClick={() => selectScale(scaleName, scaleNotes)}
                className={clsx(
                  'px-2.5 py-1 text-sm rounded border transition-all duration-base',
                  activeScale === scaleName
                    ? 'bg-primary text-white border-primary'
                    : 'bg-bg text-text border-border hover:bg-bg-secondary'
                )}
              >
                {scaleName}
              </button>
            ))}
          </div>
        </div>
      ))}

      {/* All / Clear */}
      <div className="flex gap-2 pt-1 border-t border-border">
        <button
          type="button"
          onClick={selectAll}
          className="px-3 py-1.5 text-sm rounded border border-border bg-bg text-text hover:bg-bg-secondary transition-all duration-base"
        >
          All Notes
        </button>
        <button
          type="button"
          onClick={clearAll}
          className="px-3 py-1.5 text-sm rounded border border-border bg-bg text-text hover:bg-bg-secondary transition-all duration-base"
        >
          Clear
        </button>
      </div>

      {/* Individual note toggles */}
      <div>
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2">
          Individual Notes
        </p>
        <div className="grid grid-cols-6 gap-2">
          {MUSICAL_NOTES.map((note) => (
            <button
              key={note}
              type="button"
              onClick={() => toggleNote(note)}
              className={clsx(
                'px-3 py-2 text-base font-medium rounded border transition-all duration-base',
                value.includes(note)
                  ? 'bg-primary text-white border-primary'
                  : 'bg-bg text-text border-border hover:bg-bg-secondary'
              )}
            >
              {note}
            </button>
          ))}
        </div>
      </div>

      <p className="text-sm text-text-secondary">
        {value.length} {value.length === 1 ? 'note' : 'notes'} selected
      </p>
    </div>
  )
}
