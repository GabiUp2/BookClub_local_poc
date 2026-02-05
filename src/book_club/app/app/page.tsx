'use client'

import '@/lib/tracing'
import { useEffect, useState } from 'react'
import PDFUpload from '../components/PDFUpload'
import { fetchWithTracing } from '@/lib/fetchWithTracing'

export default function Home() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8010'

  useEffect(() => {
    fetchWithTracing(`${apiBaseUrl}/health`)
      .then(res => res.json())
      .then(data => setApiStatus(`✓ API healthy (uptime: ${data.uptime_s}s)`))
      .catch(() => setApiStatus('✗ API unreachable'))
  }, [apiBaseUrl])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">Book Club</h1>
        <p className="text-center mb-4">AI-powered book club assistant</p>
        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-8">
          <p className="text-sm">
            <strong>API Status:</strong> {apiStatus}
          </p>
          <p className="text-sm mt-2">
            <strong>API Base URL:</strong> {apiBaseUrl}
          </p>
        </div>
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-center">Upload PDF</h2>
          <PDFUpload />
        </div>
        <div className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>CopilotKit integration coming next...</p>
        </div>
      </div>
    </main>
  )
}
