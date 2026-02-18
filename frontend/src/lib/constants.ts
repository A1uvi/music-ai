export const MUSICAL_NOTES = [
  'C',
  'C#',
  'D',
  'D#',
  'E',
  'F',
  'F#',
  'G',
  'G#',
  'A',
  'A#',
  'B',
] as const

// All 12 major keys, all 12 natural minor keys, plus extras.
// Notes use the sharp names that appear in MUSICAL_NOTES (flats mapped to enharmonic sharps).
export const SCALE_GROUPS = {
  Major: {
    'C':    ['C',  'D',  'E',  'F',  'G',  'A',  'B' ],
    'G':    ['G',  'A',  'B',  'C',  'D',  'E',  'F#'],
    'D':    ['D',  'E',  'F#', 'G',  'A',  'B',  'C#'],
    'A':    ['A',  'B',  'C#', 'D',  'E',  'F#', 'G#'],
    'E':    ['E',  'F#', 'G#', 'A',  'B',  'C#', 'D#'],
    'B':    ['B',  'C#', 'D#', 'E',  'F#', 'G#', 'A#'],
    'F#':   ['F#', 'G#', 'A#', 'B',  'C#', 'D#', 'F' ],
    'F':    ['F',  'G',  'A',  'A#', 'C',  'D',  'E' ],
    'Bb':   ['A#', 'C',  'D',  'D#', 'F',  'G',  'A' ],
    'Eb':   ['D#', 'F',  'G',  'G#', 'A#', 'C',  'D' ],
    'Ab':   ['G#', 'A#', 'C',  'C#', 'D#', 'F',  'G' ],
    'Db':   ['C#', 'D#', 'F',  'F#', 'G#', 'A#', 'C' ],
  },
  Minor: {
    'Am':   ['A',  'B',  'C',  'D',  'E',  'F',  'G' ],
    'Em':   ['E',  'F#', 'G',  'A',  'B',  'C',  'D' ],
    'Bm':   ['B',  'C#', 'D',  'E',  'F#', 'G',  'A' ],
    'F#m':  ['F#', 'G#', 'A',  'B',  'C#', 'D',  'E' ],
    'C#m':  ['C#', 'D#', 'E',  'F#', 'G#', 'A',  'B' ],
    'G#m':  ['G#', 'A#', 'B',  'C#', 'D#', 'E',  'F#'],
    'D#m':  ['D#', 'F',  'F#', 'G#', 'A#', 'B',  'C#'],
    'Dm':   ['D',  'E',  'F',  'G',  'A',  'A#', 'C' ],
    'Gm':   ['G',  'A',  'A#', 'C',  'D',  'D#', 'F' ],
    'Cm':   ['C',  'D',  'D#', 'F',  'G',  'G#', 'A#'],
    'Fm':   ['F',  'G',  'G#', 'A#', 'C',  'C#', 'D#'],
    'Bbm':  ['A#', 'C',  'C#', 'D#', 'F',  'F#', 'G#'],
  },
  Other: {
    'Pentatonic': ['C',  'D',  'E',  'G',  'A'         ],
    'Blues':      ['C',  'D#', 'F',  'F#', 'G',  'A#'  ],
    'Chromatic':  [...MUSICAL_NOTES],
  },
} as const

// Flat alias kept for any code that still references COMMON_SCALES
export const COMMON_SCALES: Record<string, readonly string[]> = Object.fromEntries(
  Object.values(SCALE_GROUPS).flatMap((group) => Object.entries(group))
)

export const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB

export const ALLOWED_FILE_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/mp3',
  'audio/x-wav',
  'video/mp4',
  'video/quicktime',
]
