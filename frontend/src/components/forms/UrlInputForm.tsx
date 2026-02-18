'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

interface UrlInputFormProps {
  onSubmit: (url: string) => void
  isProcessing: boolean
}

export function UrlInputForm({ onSubmit, isProcessing }: UrlInputFormProps) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    try {
      new URL(url)
    } catch {
      setError('Please enter a valid URL')
      return
    }

    onSubmit(url)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="YouTube or Music URL"
        type="url"
        placeholder="https://youtube.com/watch?v=..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={isProcessing}
      />

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
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? 'Processing...' : 'Transcribe from URL'}
      </Button>
    </form>
  )
}
