'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/Button'
import { MAX_FILE_SIZE, ALLOWED_FILE_TYPES } from '@/lib/constants'

interface FileUploadFormProps {
  onSubmit: (file: File) => void
  isProcessing: boolean
}

export function FileUploadForm({ onSubmit, isProcessing }: FileUploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    setError(null)

    if (!selectedFile) {
      setFile(null)
      return
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB`)
      setFile(null)
      return
    }

    if (!ALLOWED_FILE_TYPES.includes(selectedFile.type)) {
      setError('Invalid file type. Please upload an audio or video file.')
      setFile(null)
      return
    }

    setFile(selectedFile)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!file) {
      setError('Please select a file')
      return
    }

    onSubmit(file)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-text mb-2">
          Audio or Video File
        </label>
        <div
          className="border-2 border-dashed border-border rounded p-6 text-center cursor-pointer hover:border-primary transition-all duration-base"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_FILE_TYPES.join(',')}
            onChange={handleFileChange}
            className="hidden"
            disabled={isProcessing}
          />
          {file ? (
            <div className="space-y-1">
              <p className="text-base font-medium text-text">{file.name}</p>
              <p className="text-sm text-text-secondary">{formatFileSize(file.size)}</p>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  setFile(null)
                  if (fileInputRef.current) fileInputRef.current.value = ''
                }}
                className="text-sm text-primary hover:underline"
              >
                Remove
              </button>
            </div>
          ) : (
            <div className="space-y-1">
              <p className="text-base text-text">Click to select a file</p>
              <p className="text-sm text-text-secondary">
                MP3, WAV, MP4 (max {MAX_FILE_SIZE / 1024 / 1024}MB)
              </p>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-error bg-opacity-10 border border-error rounded text-sm text-error">
          {error}
        </div>
      )}

      <Button
        type="submit"
        variant="primary"
        size="lg"
        isLoading={isProcessing}
        disabled={isProcessing || !file}
        className="w-full"
      >
        {isProcessing ? 'Processing...' : 'Transcribe from File'}
      </Button>
    </form>
  )
}
