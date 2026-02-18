'use client'

import { useState, useCallback } from 'react'
import { Header } from '@/components/layout/Header'
import { Container } from '@/components/layout/Container'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { UrlInputForm } from '@/components/forms/UrlInputForm'
import { FileUploadForm } from '@/components/forms/FileUploadForm'
import { NoteSelectionInput } from '@/components/forms/NoteSelectionInput'
import { ProcessingStatus } from '@/components/display/ProcessingStatus'
import { SheetMusicViewer } from '@/components/display/SheetMusicViewer'
import { useTranscription } from '@/hooks/useTranscription'
import { MUSICAL_NOTES } from '@/lib/constants'

export default function Home() {
  const [inputMethod, setInputMethod] = useState<'url' | 'file'>('url')
  const [allowedNotes, setAllowedNotes] = useState<string[]>([...MUSICAL_NOTES])
  const [separateMelody, setSeparateMelody] = useState(false)

  const {
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
  } = useTranscription()

  const handleSubmitUrl = useCallback(
    (url: string) => submitUrl(url, allowedNotes, separateMelody),
    [submitUrl, allowedNotes, separateMelody],
  )

  const handleSubmitFile = useCallback(
    (file: File) => submitFile(file, allowedNotes, separateMelody),
    [submitFile, allowedNotes, separateMelody],
  )

  const showResult = result && vexflowData && !isProcessing

  return (
    <div className="min-h-screen bg-bg-secondary">
      <Header />

      <Container size="lg">
        {/* Main Content */}
        {!isProcessing && !showResult && !error && (
          <div className="space-y-6">
            {/* Input Method Toggle */}
            <div className="flex gap-2 justify-center">
              <Button
                variant={inputMethod === 'url' ? 'primary' : 'secondary'}
                onClick={() => setInputMethod('url')}
              >
                From URL
              </Button>
              <Button
                variant={inputMethod === 'file' ? 'primary' : 'secondary'}
                onClick={() => setInputMethod('file')}
              >
                Upload File
              </Button>
            </div>

            {/* Input Forms */}
            <Card>
              {inputMethod === 'url' ? (
                <UrlInputForm onSubmit={handleSubmitUrl} isProcessing={isProcessing} />
              ) : (
                <FileUploadForm onSubmit={handleSubmitFile} isProcessing={isProcessing} />
              )}

              {/* Melody separation toggle */}
              <div className="mt-4 pt-4 border-t border-border">
                <label className="flex items-center gap-3 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={separateMelody}
                    onChange={(e) => setSeparateMelody(e.target.checked)}
                    className="w-4 h-4 rounded border-border accent-primary"
                  />
                  <div>
                    <span className="text-sm font-medium text-text">
                      Separate melody
                    </span>
                    <span className="block text-xs text-text-secondary">
                      Removes drums and bass before transcription — slower but more accurate
                    </span>
                  </div>
                </label>
              </div>
            </Card>

            {/* Note Selection */}
            <Card>
              <NoteSelectionInput value={allowedNotes} onChange={setAllowedNotes} />
            </Card>

            {/* Instructions */}
            <Card variant="outlined" className="bg-bg-secondary">
              <h3 className="text-lg font-semibold text-text mb-2">
                How it works
              </h3>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside">
                <li>Provide a YouTube URL or upload an audio/video file</li>
                <li>Select which notes can appear in the transcription</li>
                <li>Detected pitches are mapped to your chosen scale or note set</li>
                <li>View and play back the resulting sheet music notation</li>
              </ol>
            </Card>
          </div>
        )}

        {/* Processing Status */}
        {isProcessing && (
          <Card>
            <ProcessingStatus stage={stage} progress={progress} logs={logs} />
          </Card>
        )}

        {/* Error Display */}
        {error && !isProcessing && (
          <Card>
            <div className="space-y-4">
              <div className="p-4 bg-error bg-opacity-10 border border-error rounded">
                <h3 className="text-base font-semibold text-error mb-1">
                  Processing Failed
                </h3>
                <p className="text-sm text-error">{error}</p>
              </div>
              <Button onClick={reset} variant="primary">
                Try Again
              </Button>
            </div>
          </Card>
        )}

        {/* Results Display */}
        {showResult && (
          <div className="space-y-6">
            <Card>
              <SheetMusicViewer
                vexflowData={vexflowData}
                metadata={result.metadata}
                notes={result.notes}
              />
            </Card>

            <Card variant="outlined">
              <h3 className="text-lg font-semibold text-text mb-3">
                Transcription Details
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-text-secondary">Notes Detected</p>
                  <p className="text-base font-medium text-text">
                    {result.metadata.note_count}
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary">Key Signature</p>
                  <p className="text-base font-medium text-text">
                    {result.metadata.key_signature}
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary">Tempo</p>
                  <p className="text-base font-medium text-text">
                    {result.metadata.tempo} BPM
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary">Time Signature</p>
                  <p className="text-base font-medium text-text">
                    {result.metadata.time_signature}
                  </p>
                </div>
              </div>
            </Card>

            <Button onClick={reset} variant="secondary" className="w-full">
              Transcribe Another
            </Button>
          </div>
        )}
      </Container>
    </div>
  )
}
