/**
 * Next.js API route that proxies OTLP/HTTP trace payloads from browser to Alloy.
 *
 * The frontend OTLP exporter POSTs to /api/otel/v1/traces; this route must exist
 * for those requests to be forwarded. Avoids CORS and exposes a single proxy point.
 */

import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

const ALLOY_OTLP_ENDPOINT = process.env.ALLOY_OTLP_ENDPOINT || 'http://alloy:4318/v1/traces'

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()

    const response = await fetch(ALLOY_OTLP_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body,
    })

    const responseText = await response.text()

    return new NextResponse(responseText, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
      },
    })
  } catch (error) {
    console.error('[OTEL Proxy] Error forwarding trace to Alloy:', error)
    return NextResponse.json(
      { error: 'Failed to forward trace to collector' },
      { status: 500 },
    )
  }
}
