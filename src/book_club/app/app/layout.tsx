import type { Metadata } from 'next'
import './globals.css'
import { CopilotProvider } from '@/components/CopilotProvider'

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
        <CopilotProvider>{children}</CopilotProvider>
      </body>
    </html>
  )
}
