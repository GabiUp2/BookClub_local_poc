/**
 * Fetch wrapper with OpenTelemetry traceparent propagation and fault injection.
 * 
 * This wrapper:
 * 1. Applies client-side delay (fault injection) before making requests
 * 2. Creates spans for fetch operations
 * 
 * Note: The fetch instrumentation automatically adds traceparent headers,
 * so we don't need to manually inject them.
 */

import { trace } from '@opentelemetry/api'

// Cache fault config (polled from API)
let cachedFaultConfig = { client_delay_ms: 0 }
let lastFaultConfigFetch = 0
const FAULT_CONFIG_CACHE_MS = 5000 // Refresh every 5 seconds

async function getFaultConfig(): Promise<{ client_delay_ms: number }> {
  const now = Date.now()
  
  // Use cached config if recent
  if (now - lastFaultConfigFetch < FAULT_CONFIG_CACHE_MS) {
    return cachedFaultConfig
  }

  try {
    const response = await fetch('/api/demo/faults')
    if (response.ok) {
      const data = await response.json()
      cachedFaultConfig = data.config || { client_delay_ms: 0 }
      lastFaultConfigFetch = now
    }
  } catch (error) {
    // Silently fail - use cached config
    console.warn('[FetchWithTracing] Failed to fetch fault config:', error)
  }

  return cachedFaultConfig
}

/**
 * Fetch wrapper with tracing and fault injection.
 * 
 * @param url - Request URL
 * @param options - Fetch options (same as native fetch)
 * @returns Promise<Response>
 */
export async function fetchWithTracing(
  url: string | URL,
  options?: RequestInit
): Promise<Response> {
  const tracer = trace.getTracer('bookclub-app')
  const urlString = typeof url === 'string' ? url : url.toString()
  
  // Check if this is a backend API call (not internal Next.js routes)
  const isBackendCall = urlString.startsWith('http://') || urlString.startsWith('https://')
  
  return tracer.startActiveSpan(
    `fetch ${urlString}`,
    {
      attributes: {
        'http.method': options?.method || 'GET',
        'http.url': urlString,
      },
    },
    async (span) => {
      try {
        // Apply client delay if configured (only for backend calls)
        if (isBackendCall) {
          const faultConfig = await getFaultConfig()
          if (faultConfig.client_delay_ms > 0) {
            await new Promise((resolve) =>
              setTimeout(resolve, faultConfig.client_delay_ms)
            )
            span.setAttribute('fault.client_delay_ms', faultConfig.client_delay_ms)
          }
        }

        // Make the fetch request
        // The fetch instrumentation will automatically add traceparent header
        const response = await fetch(urlString, options)

        // Record response attributes
        span.setAttribute('http.status_code', response.status)
        span.setAttribute('http.status_text', response.statusText)

        if (!response.ok) {
          span.setStatus({ code: 1, message: `HTTP ${response.status}` })
        }

        return response
      } catch (error) {
        // Record error
        span.recordException(error as Error)
        span.setStatus({ code: 2, message: (error as Error).message })
        throw error
      } finally {
        span.end()
      }
    }
  )
}
