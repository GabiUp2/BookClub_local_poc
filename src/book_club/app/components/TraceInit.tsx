'use client'

/**
 * Client-only mount point for OpenTelemetry tracing.
 * Importing the tracing module here ensures it runs in the browser (layout is a Server Component).
 */
import '@/lib/tracing'

export function TraceInit() {
  return null
}
