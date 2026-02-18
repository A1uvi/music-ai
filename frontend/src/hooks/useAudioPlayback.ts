'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import type { NoteData, MusicMetadata } from '@/types/api'

export type PlaybackState = 'idle' | 'playing' | 'paused'

const NOTE_SEMITONES: Record<string, number> = {
  C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3,
  E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8,
  Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11,
}

const DURATION_BEATS: Record<string, number> = {
  w: 4, hd: 3, h: 2, qd: 1.5, q: 1, '8d': 0.75, '8': 0.5, '16': 0.25,
}

// Lookahead scheduler constants — schedule notes LOOKAHEAD_SECS ahead of
// playback, refreshing every SCHEDULE_INTERVAL_MS. This avoids creating
// thousands of oscillators at once for long songs.
const LOOKAHEAD_SECS = 2.0
const SCHEDULE_INTERVAL_MS = 200

function noteToFreq(pitch: string, octave: number): number {
  const semitone = NOTE_SEMITONES[pitch] ?? 0
  const midi = (octave + 1) * 12 + semitone
  return 440 * Math.pow(2, (midi - 69) / 12)
}

function durationToSecs(duration: string, tempo: number): number {
  // Strip rest suffix ('qr' → 'q', '8dr' → '8d') before looking up beats
  const beats = DURATION_BEATS[duration.replace('r', '')] ?? 1
  return beats * (60 / tempo)
}

export function useAudioPlayback(notes: NoteData[], metadata: MusicMetadata) {
  const [playbackState, setPlaybackState] = useState<PlaybackState>('idle')
  const [currentTime, setCurrentTime] = useState(0)

  const audioCtxRef = useRef<AudioContext | null>(null)
  const oscsRef = useRef<OscillatorNode[]>([])
  const contextStartRef = useRef(0)   // audioCtx.currentTime when song position = seekOffset
  const seekOffsetRef = useRef(0)     // song position (secs) at last play/pause
  const rafRef = useRef<number | null>(null)
  const schedulerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const nextNoteIndexRef = useRef(0)  // index into sortedNotesRef up to which we've scheduled

  // Keep mutable refs for prop-derived values so scheduler callbacks don't
  // need to be rebuilt when props change.
  const sortedNotesRef = useRef<NoteData[]>(
    [...notes].sort((a, b) => a.start_time - b.start_time)
  )
  const tempoRef = useRef(metadata.tempo)
  const totalDurationRef = useRef(metadata.total_duration)

  useEffect(() => {
    sortedNotesRef.current = [...notes].sort((a, b) => a.start_time - b.start_time)
  }, [notes])

  useEffect(() => {
    tempoRef.current = metadata.tempo
    totalDurationRef.current = metadata.total_duration
  }, [metadata.tempo, metadata.total_duration])

  const cancelRaf = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
  }, [])

  const cancelScheduler = useCallback(() => {
    if (schedulerTimerRef.current !== null) {
      clearTimeout(schedulerTimerRef.current)
      schedulerTimerRef.current = null
    }
  }, [])

  const killOscillators = useCallback(() => {
    oscsRef.current.forEach((osc) => {
      try { osc.stop(0) } catch { /* already stopped */ }
    })
    oscsRef.current = []
  }, [])

  // Stable function refs — only close over other refs, so no stale closure issues.
  const scheduleNoteRef = useRef((audioCtx: AudioContext, note: NoteData) => {
    // Rests ('qr', '8r', etc.) are silent — skip oscillator creation
    if (note.duration.endsWith('r')) return

    const now = audioCtx.currentTime
    const startAt = contextStartRef.current + note.start_time
    if (startAt < now - 0.02) return  // already past

    const freq = noteToFreq(note.pitch, note.octave)
    const dur = durationToSecs(note.duration, tempoRef.current)
    const endAt = startAt + dur
    const schedStart = Math.max(startAt, now)

    const attackTime = 0.003
    const decayTime = Math.min(0.3, dur * 0.4)
    const peakGain = 0.45
    const sustainLevel = peakGain * 0.25
    const sustainEnd = Math.max(
      schedStart + attackTime + decayTime,
      endAt - Math.min(0.12, dur * 0.25)
    )

    // Primary sine (fundamental)
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.type = 'sine'
    osc.frequency.value = freq
    gain.gain.setValueAtTime(0, schedStart)
    gain.gain.linearRampToValueAtTime(peakGain, schedStart + attackTime)
    gain.gain.exponentialRampToValueAtTime(sustainLevel, schedStart + attackTime + decayTime)
    gain.gain.setValueAtTime(sustainLevel, sustainEnd)
    gain.gain.exponentialRampToValueAtTime(0.001, endAt)
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.start(schedStart)
    osc.stop(endAt)
    oscsRef.current.push(osc)

    // Second oscillator at 2× for percussive brightness
    const brightOsc = audioCtx.createOscillator()
    const brightGain = audioCtx.createGain()
    brightOsc.type = 'sine'
    brightOsc.frequency.value = freq * 2
    const brightDecay = decayTime * 0.4
    brightGain.gain.setValueAtTime(0, schedStart)
    brightGain.gain.linearRampToValueAtTime(0.06, schedStart + attackTime)
    brightGain.gain.exponentialRampToValueAtTime(0.001, schedStart + attackTime + brightDecay)
    brightOsc.connect(brightGain)
    brightGain.connect(audioCtx.destination)
    brightOsc.start(schedStart)
    brightOsc.stop(schedStart + attackTime + brightDecay + 0.01)
    oscsRef.current.push(brightOsc)
  })

  const runSchedulerRef = useRef((audioCtx: AudioContext) => {
    const playbackPos = audioCtx.currentTime - contextStartRef.current
    const scheduleUpTo = playbackPos + LOOKAHEAD_SECS
    const sorted = sortedNotesRef.current

    while (
      nextNoteIndexRef.current < sorted.length &&
      sorted[nextNoteIndexRef.current].start_time <= scheduleUpTo
    ) {
      scheduleNoteRef.current(audioCtx, sorted[nextNoteIndexRef.current])
      nextNoteIndexRef.current++
    }

    if (nextNoteIndexRef.current < sorted.length) {
      schedulerTimerRef.current = setTimeout(
        () => runSchedulerRef.current(audioCtx),
        SCHEDULE_INTERVAL_MS
      )
    }
  })

  const play = useCallback(async () => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext()
    }
    const audioCtx = audioCtxRef.current
    if (audioCtx.state === 'suspended') await audioCtx.resume()

    cancelRaf()
    cancelScheduler()
    killOscillators()

    const from = seekOffsetRef.current
    contextStartRef.current = audioCtx.currentTime - from

    // Find first note at or after the seek position
    const sorted = sortedNotesRef.current
    let idx = 0
    while (idx < sorted.length && sorted[idx].start_time < from - 0.02) idx++
    nextNoteIndexRef.current = idx

    runSchedulerRef.current(audioCtx)
    setPlaybackState('playing')

    const tick = () => {
      if (!audioCtxRef.current) return
      const elapsed = audioCtxRef.current.currentTime - contextStartRef.current
      setCurrentTime(Math.min(elapsed, totalDurationRef.current))

      if (elapsed >= totalDurationRef.current) {
        cancelScheduler()
        killOscillators()
        cancelRaf()
        seekOffsetRef.current = 0
        setPlaybackState('idle')
        setCurrentTime(0)
        return
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
  }, [cancelRaf, cancelScheduler, killOscillators])

  const pause = useCallback(() => {
    if (!audioCtxRef.current) return
    seekOffsetRef.current = audioCtxRef.current.currentTime - contextStartRef.current
    cancelRaf()
    cancelScheduler()
    killOscillators()
    setPlaybackState('paused')
    setCurrentTime(seekOffsetRef.current)
  }, [cancelRaf, cancelScheduler, killOscillators])

  const stop = useCallback(() => {
    cancelRaf()
    cancelScheduler()
    killOscillators()
    seekOffsetRef.current = 0
    setPlaybackState('idle')
    setCurrentTime(0)
  }, [cancelRaf, cancelScheduler, killOscillators])

  useEffect(() => () => {
    cancelRaf()
    cancelScheduler()
    killOscillators()
    audioCtxRef.current?.close()
  }, [cancelRaf, cancelScheduler, killOscillators])

  return { play, pause, stop, playbackState, currentTime, totalDuration: metadata.total_duration }
}
