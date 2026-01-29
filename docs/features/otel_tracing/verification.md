# OTEL Tracing — Verification

## Done vs spec

| Acceptance criterion | Status | Evidence |
|----------------------|--------|----------|
| Traces emitted and visible in Tempo | Done | Backend and frontend export via Alloy OTLP; Tempo datasource in Grafana. |
| Trace context propagation (W3C traceparent) | Done | Fetch instrumentation propagates to backend; FastAPI receives and continues trace. |
| Logs include trace_id for pivoting (Loki → Tempo) | Done | LoggingInstrumentor + log format with otelTraceID/otelSpanID; Loki query by trace_id. |
| Metrics use exemplars (Prometheus → Tempo) | Done | ExecutionTimings and IngestMetrics attach trace_id to histogram exemplars. |
| demo-healthy-trace-signal | Done | Make target resets faults, runs generate_traffic; stable latency. |
| demo-frontend-latency-issue-trace-signal | Done | POST /api/demo/faults client_delay_ms; traffic shows client delay in trace. |
| demo-server-chocking-trace-signal | Done | POST /__demo/faults cpu_burn_ms + error_rate; backend spans and p95 show impact. |
| demo-qdrant-down-trace-signal | Done | docker compose stop/start qdrant; traffic during outage shows error spans; demo-reset restores. |
| demo-reset / demo-verify | Done | Make targets; verify_signals checks Tempo, Loki, Prometheus, backend, Grafana. |

## Validation commands

```bash
# Smoke-check signals (run after stack is up and some traffic generated)
make demo-verify

# Generate healthy baseline
make demo-healthy-trace-signal

# Run demo scenarios
make demo-frontend-latency-issue-trace-signal
make demo-server-chocking-trace-signal
make demo-qdrant-down-trace-signal

# Restore baseline
make demo-reset
```

## Open gaps

- **Demo Overview dashboard**: Scaffold mentions a "Demo Overview" dashboard (p95/p99, error rate, log volume); not yet added. Existing execution timings and PDF upload dashboards show metrics and exemplars.
- **Tempo search API**: verify_signals uses Tempo search; exact API/params may vary by Tempo version; Loki uses nanoseconds and X-Scope-OrgID for multi-tenant.
- **Dependency outage**: Implemented as docker compose stop/start qdrant; optional Toxiproxy for finer fault injection not done.
