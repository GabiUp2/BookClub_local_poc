import client from 'prom-client'

type MetricsBundle = {
  register: client.Registry
  httpRequestsTotal: client.Counter<string>
}

let metricsSingleton: MetricsBundle | null = null

export function getMetrics(): MetricsBundle {
  if (metricsSingleton) return metricsSingleton

  // Ensure a dedicated registry to avoid Next dev HMR duplication
  const register = new client.Registry()
  client.collectDefaultMetrics({ register, prefix: 'bookclub_app_' })

  const httpRequestsTotal = new client.Counter({
    name: 'bookclub_app_http_requests_total',
    help: 'Total HTTP requests processed by Next.js app',
    labelNames: ['method', 'path', 'status'],
    registers: [register],
  })

  metricsSingleton = { register, httpRequestsTotal }
  return metricsSingleton
}

export async function getMetricsText(): Promise<string> {
  const { register } = getMetrics()
  return await register.metrics()
}


