# OTEL Tracing — Feature Documentation

## Overview

This feature adds **end-to-end OpenTelemetry tracing** to the BookClub Local POC. Traces start in the browser (frontend) and propagate to the FastAPI backend and dependencies. Logs and metrics are correlated with traces via `trace_id` and exemplars, so you can pivot in Grafana from metrics or logs to the same trace. A **Makefile-driven demo harness** generates reproducible "healthy" and "faulty" scenarios for presentations.

## What it adds

- **Frontend-origin traces**: Browser instrumentation (fetch) with W3C `traceparent` propagation to the backend.
- **Backend tracing**: FastAPI and `requests` auto-instrumentation, custom spans for upload flow, resource attributes (service name, env, git commit/branch).
- **Log correlation**: Log formatter and logging instrumentation inject `trace_id` and `span_id` into log lines (Loki).
- **Metric exemplars**: Key histograms (upload duration, execution timings) attach exemplars with `trace_id` (Prometheus → Tempo).
- **Demo harness**: Make targets that set fault mode, generate traffic, and print where to look in Grafana.

## User-facing behaviour

### Happy path

1. Start stack: `docker compose up -d`
2. Open the app in the browser; perform an action (e.g. upload a PDF or trigger health check).
3. Traces appear in Tempo with frontend and backend spans under one `trace_id`.
4. Logs in Loki contain `trace_id`; metrics histograms show exemplar dots that link to traces.

### Demo scenarios

| Target | Behaviour |
|--------|-----------|
| `make demo-verify` | Smoke-checks that traces, logs, and metrics are flowing (run before presenting). |
| `make demo-healthy-trace-signal` | Resets faults, generates traffic; stable latency, no injected errors. |
| `make demo-frontend-latency-issue-trace-signal` | Sets 800 ms client delay; client span shows delay before backend. |
| `make demo-server-chocking-trace-signal` | Sets backend CPU burn + 5% error rate; backend spans and p95/p99 show impact. |
| `make demo-qdrant-down-trace-signal` | Stops Qdrant, generates traffic (errors), starts Qdrant, generates recovery traffic. |
| `make demo-reset` | Resets all fault injection and ensures Qdrant is up. |

### Edge cases

- **OTEL disabled**: Set `ENABLE_OTEL_TRACING=false` (backend) or `NEXT_PUBLIC_ENABLE_OTEL_TRACING=false` (frontend) to disable tracing.
- **Demo endpoints**: `/__demo/*` (backend) and `/api/demo/*` (frontend) are only available when `APP_ENV=local` or in development; otherwise 403.

## Configuration / environment variables

### Backend (FastAPI)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_OTEL_TRACING` | `true` | Enable or disable OTEL SDK and instrumentors. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://alloy:4318` | OTLP HTTP endpoint (Alloy). |
| `OTEL_SERVICE_NAME` | `bookclub-preprocessing-server` | Service name in traces. |
| `APP_ENV` | `local` | Used for resource attribute `deployment.environment` and demo endpoint guard. |
| `ENABLE_OTEL_LOGS` | `true` | Enable logging instrumentation (trace_id/span_id in logs). |

### Frontend (Next.js)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_ENABLE_OTEL_TRACING` | (enabled) | Set to `false` to disable browser tracing. |
| `NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT` | `/api/otel` | Proxy route for OTLP/HTTP (browser → Next.js → Alloy). |
| `NEXT_PUBLIC_OTEL_SERVICE_NAME` | `bookclub-app` | Service name for frontend spans. |

### Alloy / Docker

- Alloy exposes OTLP gRPC `4317` and OTLP HTTP `4318`; backend and Next.js proxy use HTTP for export.
- Next.js app needs `ALLOY_OTLP_ENDPOINT` (e.g. `http://alloy:4318`) for the server-side proxy; default is `http://alloy:4318`.

## API / contracts summary

### Demo endpoints (backend, `APP_ENV=local` only)

- **POST `/__demo/faults`**
  Body: `{ "backend_delay_ms": 0, "cpu_burn_ms": 0, "error_rate": 0.0 }`
  Sets in-memory fault config; applied by middleware (delay, CPU burn, probabilistic 500).

- **POST `/__demo/reset`**
  Resets fault config to baseline (no delay, no burn, 0% error rate).

### Demo endpoints (frontend, development only)

- **POST `/api/demo/faults`**
  Body: `{ "client_delay_ms": 800 }`
  Sets client-side delay applied before backend fetch (demo frontend-latency scenario).

- **POST `/api/demo/reset`**
  Resets client delay to 0.

### OTLP proxy (frontend)

- **POST `/api/otel`**
  Proxies OTLP/HTTP trace export from browser to Alloy; no auth (internal use).

## Observability notes

- **Traces**: Tempo; in Explore (Tempo) use TraceQL with **quoted** string values, e.g. `{ resource.service.name = "bookclub-preprocessing-server" }` or `{ resource.service.name = "bookclub-app" }`.
- **Logs**: Loki; log lines include `trace_id` / `span_id` when logging instrumentation is enabled; use Explore to filter and jump to Tempo.
- **Metrics**: Prometheus; histograms `preprocessing_server_pdf_upload_duration_seconds`, execution-timing histograms from `@track_timing`; enable exemplars in panels and click dot to open trace.
- **Dashboards**: Use existing execution timings and PDF upload dashboards; exemplars and trace links appear where configured. A dedicated "Demo Overview" dashboard is optional (see scaffold).

## Troubleshooting: no traces in Grafana / "0 series" in TraceQL

**"0 series returned" in TraceQL (selector query):** In Grafana Explore → Tempo → TraceQL tab, set **Run type** to **Trace** (not Metrics). A selector like `{ resource.service.name = "bookclub-preprocessing-server" }` with Run type **Metrics** returns metric series; with no metrics you see "0 series". With Run type **Trace** the same query returns trace IDs.

**Note:** `make demo-verify` / `demo-verify-with-traffic` can be all green even when Tempo has **no** traces (it only checks that Tempo is reachable). To confirm traces exist, use the Search tab or the curl below.

**If TraceQL returns "0 series" (with Run type Trace) or Search returns no traces:**

1. **Rebuild and recreate the backend** so OTEL runs in each Gunicorn worker (post_fork fix):
   ```bash
   docker compose build bookclub-preprocessing-server
   docker compose up -d --force-recreate bookclub-preprocessing-server
   ```
2. **Generate traffic** and wait for OTLP flush:
   ```bash
   make demo-healthy-trace-signal
   sleep 15
   ```
3. **In Grafana Explore (Tempo)** use the **Search** tab (not TraceQL): add a tag filter `service.name` = `bookclub-preprocessing-server` and run the search. You should see a list of traces. The TraceQL tab returns trace spans; "0 series" often means no data in Tempo yet.
4. **Check from the host** whether Tempo has any traces:
   ```bash
   curl -s "http://localhost:3200/api/search?tags=service.name%3Dbookclub-preprocessing-server&limit=5&start=$(($(date +%s) - 600))&end=$(date +%s)" | jq .traces
   ```
   If `traces` is `[]`, the pipeline is not delivering; ensure step 1 and 2 are done.

**Other checks:**

5. **Gunicorn fork-safe**: The backend uses `gunicorn.conf.py` with a `post_fork` hook so OTEL is initialised in each worker after fork. Without this, traces may not be exported. Ensure the container runs Gunicorn with `-c gunicorn.conf.py`.
6. **Backend OTLP endpoint**: Backend must send traces to Alloy. If you use a `.env` copied from `.env.example`, ensure `OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4318` (not `grafana-agent`). Restart the preprocessing server after changing.
7. **Where to look**: Grafana → **Explore** → datasource **Tempo**. Use the **Search** tab and filter by tag `service.name` = `bookclub-preprocessing-server`; or use the TraceQL tab with `{ resource.service.name = "bookclub-preprocessing-server" }` and ensure the query type is **trace** (not metrics). Use a recent time range (e.g. Last 15 minutes).
8. **Generate traffic**: Traces only appear when requests hit the app. Run `make demo-healthy-trace-signal` to generate traffic, then query Tempo.
9. **Verify pipeline**: `make demo-verify` checks that Tempo returns traces and logs contain `trace_id`; fix any failing check first.

## Operational notes

- **Rollout**: Enable by default in local/demo; disable via env vars above if needed.
- **Rollback**: Set `ENABLE_OTEL_TRACING=false` and `NEXT_PUBLIC_ENABLE_OTEL_TRACING=false`; restart backend and frontend. No schema or migration rollback.
- **Dependency outage demo**: `make demo-qdrant-down-trace-signal` stops Qdrant; run `make demo-reset` after to restore.

## Testing notes

- **Unit tests**: `tests/observability/test_demo_generate_traffic.py`, `tests/observability/test_demo_verify_signals.py` (traffic generator and signal verification).
- **Local validation**:
  1. `docker compose up -d`
  2. `make demo-verify` (expect all checks pass after some traffic)
  3. `make demo-healthy-trace-signal` then open Grafana → Explore (Tempo): recent traces for `bookclub-preprocessing-server` / `bookclub-app`.
- **CI**: Run `make test`; demo scripts are unit-tested; full demo flow is manual or optional integration job.

## See also

- [Spec](spec.md) — goals, acceptance criteria, constraints.
- [Verification](verification.md) — evidence and open gaps vs spec.
- [Scaffold export](../../otel_tracing_feature_scaffold.md) — original full scaffold (plans, runbook, changelog).
