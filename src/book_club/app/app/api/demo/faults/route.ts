/**
 * Demo fault injection endpoint for frontend latency scenarios.
 * 
 * Only available in local/dev environment.
 */

import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

// In-memory fault config (per-process, resets on restart)
// Export for access from reset endpoint
export let faultConfig = {
  client_delay_ms: 0,
}

export async function POST(request: NextRequest) {
  // Only allow in local/dev
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      { error: 'Demo endpoints only available in development' },
      { status: 403 }
    )
  }

  try {
    const body = await request.json()
    
    // Update fault config
    if (typeof body.client_delay_ms === 'number') {
      faultConfig.client_delay_ms = Math.max(0, body.client_delay_ms)
    }

    return NextResponse.json({
      status: 'ok',
      config: faultConfig,
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Invalid request body' },
      { status: 400 }
    )
  }
}

export async function GET() {
  // Only allow in local/dev
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      { error: 'Demo endpoints only available in development' },
      { status: 403 }
    )
  }

  return NextResponse.json({
    status: 'ok',
    config: faultConfig,
  })
}

// Export config getter for use in fetch wrapper
export function getFaultConfig() {
  return faultConfig
}
