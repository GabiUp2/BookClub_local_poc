import { NextResponse } from 'next/server'
import { getMetricsText } from '@/lib/metrics'

export const dynamic = 'force-dynamic'

export async function GET() {
  const text = await getMetricsText()
  return new NextResponse(text, {
    status: 200,
    headers: { 'Content-Type': 'text/plain; version=0.0.4; charset=utf-8' },
  })
}


