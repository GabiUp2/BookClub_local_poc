'use client'

import { CopilotKit } from '@copilotkit/react-core'
import { CopilotSidebar } from '@copilotkit/react-ui'
import '@copilotkit/react-ui/styles.css'

interface CopilotProviderProps {
  children: React.ReactNode
}

export function CopilotProvider({ children }: CopilotProviderProps) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8010'

  return (
    <CopilotKit
      runtimeUrl={`${apiBaseUrl}/copilotkit`}
      // For now, we'll use a placeholder endpoint
      // You'll need to implement /copilotkit endpoint in FastAPI
    >
      <CopilotSidebar
        defaultOpen={false}
        clickOutsideToClose={true}
        labels={{
          title: 'Book Club Assistant',
          initial: 'Hi! I can help you with your book club activities.',
        }}
      >
        {children}
      </CopilotSidebar>
    </CopilotKit>
  )
}
