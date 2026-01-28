/**
 * OpenTelemetry browser-side tracing initialisation.
 * 
 * Initialises OTEL SDK for browser, instruments fetch, and exports spans
 * via Next.js API route proxy to Alloy.
 */

import { WebTracerProvider } from '@opentelemetry/sdk-trace-web'
import { Resource } from '@opentelemetry/resources'
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION } from '@opentelemetry/semantic-conventions'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base'
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch'
import { registerInstrumentations } from '@opentelemetry/instrumentation'
import { trace } from '@opentelemetry/api'

let provider: WebTracerProvider | null = null

export function initTracing(): void {
  // Only initialise once
  if (provider !== null) {
    return
  }

  // Check if tracing is enabled (default: enabled in local/dev)
  const enableTracing = process.env.NEXT_PUBLIC_ENABLE_OTEL_TRACING !== 'false'
  if (!enableTracing) {
    console.log('[OTEL] Tracing disabled via NEXT_PUBLIC_ENABLE_OTEL_TRACING')
    return
  }

  try {
    // OTLP exporter endpoint - proxy via Next.js API route
    const otlpEndpoint = process.env.NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT || '/api/otel'
    
    // Service name from env or default
    const serviceName = process.env.NEXT_PUBLIC_OTEL_SERVICE_NAME || 'bookclub-app'
    const serviceVersion = process.env.NEXT_PUBLIC_OTEL_SERVICE_VERSION || '0.1.0'

    // Resource attributes
    const resource = new Resource({
      [SEMRESATTRS_SERVICE_NAME]: serviceName,
      [SEMRESATTRS_SERVICE_VERSION]: serviceVersion,
      'deployment.environment': process.env.NODE_ENV || 'development',
    })

    // OTLP exporter (HTTP)
    // The exporter will append /v1/traces if not present
    const exporter = new OTLPTraceExporter({
      url: otlpEndpoint.endsWith('/v1/traces') ? otlpEndpoint : `${otlpEndpoint}/v1/traces`,
      headers: {},
    })

    // Create Web Tracer Provider
    provider = new WebTracerProvider({
      resource,
    })

    // Add batch span processor with OTLP exporter
    provider.addSpanProcessor(new BatchSpanProcessor(exporter))

    // Register the provider globally
    provider.register()

    // Register fetch instrumentation
    registerInstrumentations({
      instrumentations: [
        new FetchInstrumentation({
          propagateTraceHeaderCorsUrls: [
            // Allow propagation to backend
            /^http:\/\/localhost:8010/,
            /^http:\/\/bookclub-preprocessing-server:8010/,
            // Allow any URL matching the API base URL pattern
            new RegExp(process.env.NEXT_PUBLIC_API_BASE_URL || '.*'),
          ],
          clearTimingResources: true,
        }),
      ],
      tracerProvider: provider,
    })

    console.log(`[OTEL] Tracing initialised: service=${serviceName}, endpoint=${otlpEndpoint}`)
  } catch (error) {
    console.error('[OTEL] Failed to initialise tracing:', error)
  }
}

/**
 * Get the current tracer for manual span creation.
 */
export function getTracer(name: string = 'bookclub-app') {
  return trace.getTracer(name)
}

// Auto-initialise when module loads (client-side only)
if (typeof window !== 'undefined') {
  initTracing()
}
