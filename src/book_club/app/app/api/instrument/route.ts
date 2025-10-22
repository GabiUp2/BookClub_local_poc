import { NextResponse } from 'next/server'
import { getMetrics } from '@/lib/metrics'

export const dynamic = 'force-dynamic'

export async function POST() {
  const { httpRequestsTotal } = getMetrics()
  httpRequestsTotal.labels('GET', '/', '200').inc()
  return NextResponse.json({ ok: true })
}


