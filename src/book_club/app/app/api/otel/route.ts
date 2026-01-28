/**
 * Next.js API route that proxies OTLP/HTTP traces from browser to Alloy.
 * 
 * This avoids CORS issues and provides a controlled proxy point for demo scenarios.
 */

import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

// Alloy OTLP HTTP endpoint (internal Docker network)
// OTLP HTTP uses /v1/traces path
const ALLOY_OTLP_ENDPOINT = process.env.ALLOY_OTLP_ENDPOINT || 'http://alloy:4318/v1/traces'

export async function POST(request: NextRequest) {
  try {
    // Get the request body (OTLP JSON)
    const body = await request.text()
    
    // Forward to Alloy
    const response = await fetch(ALLOY_OTLP_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Preserve any custom headers if needed
      },
      body,
    })

    // Forward response status and headers
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
      { status: 500 }
    )
  }
}
