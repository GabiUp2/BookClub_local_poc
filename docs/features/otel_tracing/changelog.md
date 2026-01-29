# OTEL Tracing — Changelog

## 2026-01-28

- Added OTEL tracing scaffold and implementation:
  - Backend: OTEL SDK init, FastAPI/requests instrumentation, log correlation (trace_id/span_id), metric exemplars, custom spans for upload flow, demo fault injection endpoints (`/__demo/faults`, `/__demo/reset`).
  - Frontend: Browser tracing, Next.js OTLP proxy (`/api/otel`), demo fault endpoints (`/api/demo/faults`, `/api/demo/reset`), fetch wrapper with trace propagation and client delay.
  - Alloy: OTLP HTTP receiver (4318) alongside gRPC (4317).
  - Demo harness: Make targets (demo-healthy-trace-signal, demo-frontend-latency-issue-trace-signal, demo-server-chocking-trace-signal, demo-qdrant-down-trace-signal, demo-reset, demo-verify), Python traffic generator and signal verification scripts.
- Unit tests for demo scripts: `tests/observability/test_demo_generate_traffic.py`, `tests/observability/test_demo_verify_signals.py`.
- Documentation: `docs/features/otel_tracing/` (spec, feature, verification, changelog); ROADMAP and README updated.
