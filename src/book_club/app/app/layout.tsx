import type { Metadata } from 'next'
import './globals.css'
import { CopilotProvider } from '@/components/CopilotProvider'
import { TraceInit } from '@/components/TraceInit'

export const metadata: Metadata = {
  title: 'Book Club',
  description: 'AI-powered book club assistant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <TraceInit />
        <CopilotProvider>{children}</CopilotProvider>
      </body>
    </html>
  )
}
