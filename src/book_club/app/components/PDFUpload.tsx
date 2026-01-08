'use client'

import { useState, useCallback, useRef } from 'react'

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error'
  message: string
  filename?: string
}

export default function PDFUpload() {
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
    message: '',
  })
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8010'

  const uploadFile = useCallback(async (file: File) => {
    // Validate file type
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setUploadState({
        status: 'error',
        message: 'Please select a PDF file.',
      })
      return
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      setUploadState({
        status: 'error',
        message: `File too large: ${(file.size / (1024 * 1024)).toFixed(1)}MB exceeds 50MB limit.`,
      })
      return
    }

    setUploadState({
      status: 'uploading',
      message: `Uploading ${file.name}...`,
    })

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${apiBaseUrl}/upload-pdf`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data = await response.json()
      setUploadState({
        status: 'success',
        message: data.message || 'PDF uploaded successfully.',
        filename: data.filename,
      })
    } catch (error) {
      setUploadState({
        status: 'error',
        message: error instanceof Error ? error.message : 'Upload failed. Please try again.',
      })
    }
  }, [apiBaseUrl])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadFile(file)
    }
  }, [uploadFile])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      uploadFile(file)
    }
  }, [uploadFile])

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const resetUpload = () => {
    setUploadState({ status: 'idle', message: '' })
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const statusStyles = {
    idle: 'border-gray-300 dark:border-gray-600',
    uploading: 'border-blue-400 bg-blue-50 dark:bg-blue-900/20',
    success: 'border-green-400 bg-green-50 dark:bg-green-900/20',
    error: 'border-red-400 bg-red-50 dark:bg-red-900/20',
  }

  const dragStyles = dragActive
    ? 'border-blue-500 bg-blue-100 dark:bg-blue-900/30'
    : ''

  return (
    <div className="w-full max-w-md mx-auto">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center
          transition-all duration-200 cursor-pointer
          hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-800
          ${statusStyles[uploadState.status]}
          ${dragStyles}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleClick()}
        aria-label="Upload PDF file"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handleFileSelect}
          className="hidden"
          aria-hidden="true"
        />

        {uploadState.status === 'idle' && (
          <>
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              <span className="font-semibold text-blue-600 dark:text-blue-400">
                Click to upload
              </span>{' '}
              or drag and drop
            </p>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
              PDF files only (max 50MB)
            </p>
          </>
        )}

        {uploadState.status === 'uploading' && (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
            <p className="mt-4 text-sm text-blue-600 dark:text-blue-400">
              {uploadState.message}
            </p>
          </div>
        )}

        {uploadState.status === 'success' && (
          <div className="flex flex-col items-center">
            <svg
              className="h-10 w-10 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <p className="mt-4 text-sm text-green-600 dark:text-green-400">
              {uploadState.message}
            </p>
            {uploadState.filename && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-500 break-all">
                Saved as: {uploadState.filename}
              </p>
            )}
          </div>
        )}

        {uploadState.status === 'error' && (
          <div className="flex flex-col items-center">
            <svg
              className="h-10 w-10 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            <p className="mt-4 text-sm text-red-600 dark:text-red-400">
              {uploadState.message}
            </p>
          </div>
        )}
      </div>

      {(uploadState.status === 'success' || uploadState.status === 'error') && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            resetUpload()
          }}
          className="mt-4 w-full py-2 px-4 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300
                     rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-sm"
        >
          Upload another PDF
        </button>
      )}
    </div>
  )
}
