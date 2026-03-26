# OTEL Tracing — Feature Spec

## Summary

Add end-to-end OpenTelemetry tracing to the BookClub Local POC such that **traces originate in the frontend** and propagate across service boundaries (frontend → backend → dependencies). Enable **three-signal correlation** in Grafana: metrics ↔ logs ↔ traces. Provide a **Makefile-driven demo harness** that generates deterministic "healthy" and "faulty" scenarios, including a **dependency outage**.

## Motivation

This repo is used both for development and as **presentation material** demonstrating observability in distributed systems. The feature must therefore be:

- reproducible (`docker compose up` + `make demo-*`)
- visible (clear symptoms in dashboards/explore)
- explainable (trace waterfall + correlated logs + metric symptom)

## Goals

1. Traces are emitted and visible in Tempo.
2. Trace context propagation from frontend to backend (W3C `traceparent`).
3. Logs include `trace_id` for pivoting in Grafana Explore (Loki → Tempo).
4. Metrics use exemplars for pivoting (Prometheus → Tempo) on key histograms.
5. Demo harness supports:
   - healthy baseline
   - frontend latency issue
   - backend choking/saturation issue
   - dependency outage (Qdrant down)
   and produces obvious signal in **traces + logs + metrics**.

## Non-goals

- Production security hardening (auth, TLS, multi-tenant).
- A full RUM product; only enough browser tracing for propagation + demo.
- Automated screenshot/video generation.

## Key design decisions

- **Collector**: Alloy is the central OTLP receiver; it forwards traces to Tempo and ships logs to Loki.
- **OTLP protocol**: enable both OTLP/HTTP (4318) and OTLP/gRPC (4317) at the collector. Prefer **OTLP/HTTP** for browser compatibility.
- **Browser export**: browser spans export via a Next.js proxy endpoint (`/api/otel`) to avoid CORS/security fragility.
- **Sampling**: AlwaysOn in local/demo; configurable later.
- **Fault injection**:
  - frontend latency: runtime toggle (Next.js API route `/api/demo/faults`)
  - backend choking: runtime toggle (FastAPI `/__demo/faults`)
  - dependency outage: orchestrated via compose (stop/start qdrant).

## Acceptance criteria

### Base

- A user action triggered from the browser produces a trace in Tempo with:
  - service spans for frontend and backend
  - consistent `trace_id` across spans
- Loki logs contain `trace_id` for the same request
- Prometheus histogram samples (upload latency + execution timings) have exemplars that link to the trace

### Demo harness

- `make demo-healthy-trace-signal` generates traces + logs + stable latency metrics
- `make demo-frontend-latency-issue-trace-signal` produces:
  - long client span(s) before backend spans begin
  - a metric symptom (end-to-end / client-side request duration increases)
  - logs still correlate to the same trace_id
- `make demo-server-chocking-trace-signal` produces:
  - backend spans showing slow handling / "busy" symptoms
  - p95/p99 latency spike in backend metrics
  - optional increased error rate (configurable)
  - logs correlate to trace_id
- `make demo-qdrant-down-trace-signal` produces:
  - backend traces containing dependency spans marked as error (connection refused/timeout)
  - metrics show increased error counts and/or retries
  - logs clearly show the dependency failure and include trace_id
  - `make demo-reset` returns system to healthy state after the scenario

## Constraints / compatibility

- Must not break existing Prometheus multiprocess setup (Gunicorn multiprocess metrics).
- Must run entirely containerised with Docker Compose.

## Open questions

- For dependency outage: add a dedicated fault proxy (e.g. Toxiproxy) later, or keep simple `docker compose stop/start qdrant` orchestration?
