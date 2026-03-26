/**
 * Reset demo fault injection to baseline.
 */

import { NextResponse } from 'next/server'
import { faultConfig } from '../faults/route'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

export async function POST() {
  // Only allow in local/dev
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      { error: 'Demo endpoints only available in development' },
      { status: 403 }
    )
  }

  // Reset to baseline
  faultConfig.client_delay_ms = 0

  return NextResponse.json({
    status: 'ok',
    config: faultConfig,
  })
}
