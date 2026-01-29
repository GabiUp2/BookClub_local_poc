# OTEL Tracing — Master Plan

This feature is **implemented**. The following summarises the phases that were executed; the full scaffold (including per-area plans) lives in [docs/otel_tracing_feature_scaffold.md](../../otel_tracing_feature_scaffold.md).

## Phases (completed)

1. **Phase 0 — Topology + demo harness scaffolding**  
   Demo scenarios and fault injection approach defined; traffic generator (Python script) and Make targets added.

2. **Phase 1 — Backend tracing + correlation**  
   OTEL SDK init in FastAPI; FastAPI/requests instrumentation; trace context in logs; exemplars on histograms; custom spans; `/__demo/faults` and `/__demo/reset`; Qdrant span error handling.

3. **Phase 2 — Frontend-origin traces**  
   Browser tracing; Next.js OTLP proxy (`/api/otel`); traceparent propagation; `/api/demo/faults` and `/api/demo/reset`; fetch wrapper with client delay.

4. **Phase 3 — Demo polish**  
   Make targets produce predictable signal; `demo-verify` and `demo-reset`; dependency outage via `docker compose stop/start qdrant`.

5. **Phase 4 — Testing**  
   Unit tests for `generate_traffic` and `verify_signals`; Loki API compatibility (nanoseconds, X-Scope-OrgID).

## Contracts

- **Backend**: `POST /__demo/faults`, `POST /__demo/reset` (local only). OTLP export to Alloy HTTP 4318.
- **Frontend**: `POST /api/otel` (OTLP proxy), `POST /api/demo/faults`, `POST /api/demo/reset` (dev only).
- **Make**: `demo-healthy-trace-signal`, `demo-frontend-latency-issue-trace-signal`, `demo-server-chocking-trace-signal`, `demo-qdrant-down-trace-signal`, `demo-reset`, `demo-verify`.

## Risks / rollback

- Disable tracing: `ENABLE_OTEL_TRACING=false` (backend), `NEXT_PUBLIC_ENABLE_OTEL_TRACING=false` (frontend).
- No DB migrations; rollback is config-only and restart.
