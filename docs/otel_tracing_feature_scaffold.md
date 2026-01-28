# Feature scaffold export: otel_tracing

This document contains the full scaffold text for the feature **`otel_tracing`**, laid out as **file-by-file markdown** so you can copy it into:
`docs/features/otel_tracing/...`

It includes the demo harness targets:

- `demo-healthy-trace-signal`
- `demo-frontend-latency-issue-trace-signal`
- `demo-server-chocking-trace-signal`
- `demo-qdrant-down-trace-signal` *(dependency outage)*
- `demo-reset` *(recommended)*
- `demo-verify` *(recommended)*

It also includes the end-of-work repo updates required by your standard scaffold:
- update `ROADMAP.md`
- update `README.md`
- update any existing feature Change Log section and any global changelog file (if present)

---

## docs/features/otel_tracing/spec.md

### Summary
Add end-to-end OpenTelemetry tracing to the BookClub Local POC such that **traces originate in the frontend** and propagate across service boundaries (frontend → backend → dependencies). Enable **three-signal correlation** in Grafana: metrics ↔ logs ↔ traces. Provide a **Makefile-driven demo harness** that generates deterministic “healthy” and “faulty” scenarios, including a **dependency outage**.

### Motivation
This repo is used both for development and as **presentation material** demonstrating observability in distributed systems. The feature must therefore be:

- reproducible (`docker compose up` + `make demo-*`)
- visible (clear symptoms in dashboards/explore)
- explainable (trace waterfall + correlated logs + metric symptom)

### Goals
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

### Non-goals
- Production security hardening (auth, TLS, multi-tenant).
- A full RUM product; only enough browser tracing for propagation + demo.
- Automated screenshot/video generation.

### Key design decisions
- **Collector**: Alloy is the central OTLP receiver; it forwards traces to Tempo and ships logs to Loki.
- **OTLP protocol**: enable both OTLP/HTTP (4318) and OTLP/gRPC (4317) at the collector. Prefer **OTLP/HTTP** for browser compatibility.
- **Browser export**: browser spans export via a Next.js proxy endpoint (recommended) to avoid CORS/security fragility.
- **Sampling**: AlwaysOn in local/demo; configurable later.
- **Fault injection**:
  - frontend latency: runtime toggle (Next API route)
  - backend choking: runtime toggle (FastAPI demo endpoints)
  - dependency outage: orchestrated via compose (stop/start qdrant) or a proxy (optional future enhancement)

### Acceptance criteria

#### Base
- A user action triggered from the browser produces a trace in Tempo with:
  - service spans for frontend and backend
  - consistent `trace_id` across spans
- Loki logs contain `trace_id` for the same request
- Prometheus histogram samples (upload latency + execution timings) have exemplars that link to the trace

#### Demo harness
- `make demo-healthy-trace-signal` generates traces + logs + stable latency metrics
- `make demo-frontend-latency-issue-trace-signal` produces:
  - long client span(s) before backend spans begin
  - a metric symptom (end-to-end / client-side request duration increases)
  - logs still correlate to the same trace_id
- `make demo-server-chocking-trace-signal` produces:
  - backend spans showing slow handling / “busy” symptoms
  - p95/p99 latency spike in backend metrics
  - optional increased error rate (configurable)
  - logs correlate to trace_id
- `make demo-qdrant-down-trace-signal` produces:
  - backend traces containing dependency spans marked as error (connection refused/timeout)
  - metrics show increased error counts and/or retries
  - logs clearly show the dependency failure and include trace_id
  - `make demo-reset` returns system to healthy state after the scenario

### Constraints / compatibility
- Must not break existing Prometheus multiprocess setup (Gunicorn multiprocess metrics).
- Must run entirely containerised with Docker Compose.

### Open questions
- For dependency outage: do we want to add a dedicated fault proxy (e.g., Toxiproxy) later, or keep the simple `docker compose stop/start qdrant` orchestration?

---

## docs/features/otel_tracing/plan.master.md

### Phase 0 — topology + demo harness scaffolding
- Define “demo scenarios” and how faults are injected (without manual edits).
- Add a traffic generator (container or script) used by Make targets.

### Phase 1 — backend tracing + correlation
- Initialise OTEL SDK in FastAPI at startup.
- Instrument FastAPI + requests.
- Inject trace context into logs.
- Add exemplars to key histograms.

### Phase 2 — frontend-origin traces
- Add frontend tracing (browser) and ensure propagation via `traceparent`.
- Export browser spans via a Next.js proxy endpoint that forwards OTLP/HTTP to Alloy.

### Phase 3 — demo polish
- Make targets produce predictable signal within ~10–30 seconds.
- Add a short “demo runbook” section to `feature.md`.
- Add smoke checks (`demo-verify`) and resets (`demo-reset`) for stage reliability.
- Add dependency outage orchestration target and validate that it reliably generates error traces.

---

## docs/features/otel_tracing/plan.backend.md

### Backend tracing + propagation
- Implement `_init_otel()` and call from FastAPI lifespan startup.
- Resource attributes:
  - `service.name=bookclub-preprocessing-server`
  - `deployment.environment` from `APP_ENV`
  - `git.commit`, `git.branch` (best-effort; safe fallbacks)
- Auto-instrumentation:
  - FastAPI instrumentation (server spans)
  - requests instrumentation (client spans)

### Custom spans (minimal but demo-friendly)
Add explicit spans in the backend request path so the trace waterfall “tells a story”, e.g.:
- `/upload-pdf`: `pdf.read`, `pdf.parse`, `chunk`, `embed`, `qdrant.upsert`
Even if some steps are placeholders, the boundaries help the demo.

### Log correlation
- Ensure log formatter includes `trace_id` and `span_id` as JSON fields.

### Metrics exemplars
- Attach exemplars to headline histograms:
  - upload duration histogram
  - execution timing histograms
- Exemplar content should include `trace_id` from current OTEL context.

### Backend fault injection hooks (for Makefile orchestration)
Implement runtime endpoints so you can trigger faults without restarting containers:

- `POST /__demo/faults` sets an in-memory config
  - `backend_delay_ms` (sleep)
  - `cpu_burn_ms` (busy-loop)
  - `error_rate` (probabilistic error)
- `POST /__demo/reset` resets config to baseline

The request handler should:
- apply faults early in the request (so traces show the effect clearly)
- record any forced failures as span errors (status=ERROR + exception attributes)

### Dependency outage readiness (Qdrant)
For the outage demo:
- Ensure the backend’s Qdrant calls:
  - produce spans with clear naming (`qdrant.upsert`, `qdrant.query`)
  - set span status to ERROR on exceptions
  - log one concise error line containing the exception summary + `trace_id`
- Optional (nice-to-have): add a small bounded retry with backoff, so the trace shows retries (but don’t overcomplicate).

---

## docs/features/otel_tracing/plan.frontend.md

### Minimum for “frontend-origin traces”
- Instrument browser-side tracing for fetch/XHR so requests to the backend carry `traceparent`.
- Ensure a user action from the UI triggers the backend call (not only SSR).

### Export strategy (recommended for demo stability)
Browser spans POST to a Next.js route (`/api/otel`) which forwards OTLP/HTTP to Alloy.
- avoids CORS fights
- avoids exposing collector ports to the browser
- gives you a single controlled choke point for demo toggles

### Frontend fault injection hook (latency scenario)
Provide an easy toggle that Make can set at runtime:
- `POST /api/demo/faults` with JSON, e.g. `{"client_delay_ms":800}`
- `POST /api/demo/reset`

Client delay should be applied in the code path immediately before firing the backend request, so the trace shows the delay as part of the client span timing.

---

## docs/features/otel_tracing/plan.observability.md

### Collector (Alloy)
- Ensure OTLP receivers:
  - gRPC 4317
  - HTTP 4318
- Forward traces to Tempo.

### Tempo
- Ensure traces are searchable by:
  - service name
  - environment
  - (optional) route / operation name

### Grafana
Create or extend dashboards to support the live demo:
- “Demo Overview” dashboard with:
  - backend request duration p95/p99
  - backend error rate
  - log volume
  - links/instructions for pivots (metrics → trace; logs → trace)

### Correlation
- Loki:
  - ensure `trace_id` is present in log entries and parsed as a field
  - provide a saved Explore query for demo use
- Prometheus:
  - ensure exemplars are enabled and visible on the chosen histograms
  - provide a panel where exemplar dots are easy to click

---

## docs/features/otel_tracing/plan.devops.md

### Makefile demo harness (core requirement)
Add Make targets that:
1) set fault mode (frontend/backend/dependency)
2) generate traffic for N seconds
3) print “where to look” hints (dashboard + Explore queries)

#### Required targets
- `demo-healthy-trace-signal`
- `demo-frontend-latency-issue-trace-signal`
- `demo-server-chocking-trace-signal`
- `demo-qdrant-down-trace-signal`

#### Recommended targets
- `demo-reset` — returns the system to baseline quickly
- `demo-verify` — smoke check that traces/logs/metrics are flowing before presenting

### Traffic generation
Use one of:
- a `trafficgen` container in compose (k6/hey/vegeta), or
- a small script invoked from Makefile

For presentation reliability, a containerised traffic generator is preferred.

### Dependency outage orchestration (Qdrant down)
Implement outage via Make orchestration:

**Baseline approach (simple, works in containers):**
- `docker compose stop qdrant`
- generate traffic (backend should error quickly)
- `docker compose start qdrant`
- optionally wait for readiness
- run another short traffic burst to show recovery

**Optional future enhancement (if you want more realism later):**
- add a proxy (e.g., Toxiproxy) between backend and Qdrant so you can simulate:
  - latency
  - packet loss
  - connection resets
  without restarting the container

### Makefile target skeleton
(Adjust service names/ports to your repo.)

```make
.PHONY:   demo-healthy-trace-signal   demo-frontend-latency-issue-trace-signal   demo-server-chocking-trace-signal   demo-qdrant-down-trace-signal   demo-reset demo-verify

demo-healthy-trace-signal:
	@$(MAKE) demo-reset
	@echo "Setting faults: healthy"
	@curl -sS -X POST http://localhost:8010/__demo/reset >/dev/null || true
	@curl -sS -X POST http://localhost:8000/api/demo/reset >/dev/null || true
	@$(MAKE) _demo-traffic
	@$(MAKE) _demo-hints

demo-frontend-latency-issue-trace-signal:
	@$(MAKE) demo-reset
	@echo "Setting faults: frontend latency"
	@curl -sS -X POST http://localhost:8000/api/demo/faults -H 'content-type: application/json' 		-d '{"client_delay_ms":800}' >/dev/null
	@$(MAKE) _demo-traffic
	@$(MAKE) _demo-hints

demo-server-chocking-trace-signal:
	@$(MAKE) demo-reset
	@echo "Setting faults: server choking"
	@curl -sS -X POST http://localhost:8010/__demo/faults -H 'content-type: application/json' 		-d '{"backend_delay_ms":0,"cpu_burn_ms":600,"error_rate":0.05}' >/dev/null
	@$(MAKE) _demo-traffic
	@$(MAKE) _demo-hints

demo-qdrant-down-trace-signal:
	@$(MAKE) demo-reset
	@echo "Scenario: Qdrant dependency outage"
	@echo "Stopping qdrant..."
	@docker compose stop qdrant
	@echo "Generating traffic against backend (should fail fast)..."
	@$(MAKE) _demo-traffic
	@echo "Starting qdrant..."
	@docker compose start qdrant
	@echo "Waiting briefly for qdrant readiness..."
	@sleep 3
	@echo "Generating recovery traffic..."
	@$(MAKE) _demo-traffic
	@$(MAKE) _demo-hints

demo-reset:
	@echo "Resetting faults to baseline"
	@curl -sS -X POST http://localhost:8010/__demo/reset >/dev/null || true
	@curl -sS -X POST http://localhost:8000/api/demo/reset >/dev/null || true
	@echo "Ensuring qdrant is up"
	@docker compose start qdrant >/dev/null 2>&1 || true

demo-verify:
	@echo "Smoke-checking signals (tempo/loki/prometheus)..."
	@python -m observability.demo.verify_signals

_demo-traffic:
	@echo "Generating traffic..."
	@python -m observability.demo.generate_traffic --seconds 20 --concurrency 5

_demo-hints:
	@echo "Open Grafana: http://localhost:3000"
	@echo "Dashboard: Demo Overview"
	@echo "Explore pivots: Metrics -> exemplars -> trace; Logs -> trace_id -> trace"
```

---

## docs/features/otel_tracing/verification.md

### Manual verification (base)
1. Start the stack: `docker compose up -d`
2. Trigger a browser action that calls the backend.
3. Confirm in Grafana:
   - Tempo: trace exists for the operation
   - Loki: logs include `trace_id` for the same request
   - Prometheus: chosen histograms show exemplars (click dot → trace)

### Scenario verification

#### `demo-healthy-trace-signal`
- Stable latency distributions
- No elevated error rates
- Trace shows normal waterfall

#### `demo-frontend-latency-issue-trace-signal`
- Client span shows delay before backend spans begin
- Overall request latency increases
- Trace is still correlated end-to-end

#### `demo-server-chocking-trace-signal`
- Backend spans show prolonged durations (delay/busy-loop)
- p95/p99 spike in backend metrics
- optional errors appear (if configured)
- logs show trace_id and clear “fault mode” markers

#### `demo-qdrant-down-trace-signal`
- During outage window:
  - dependency span(s) error (connection refused/timeout)
  - backend request spans are marked error when appropriate
  - metrics show error increase
  - logs show dependency failure with trace_id
- After recovery:
  - traffic returns to healthy
  - traces show successful dependency spans
  - errors drop

### `demo-verify` smoke checks (recommended)
Implement simple checks:
- Tempo: find a recent trace by `service.name`
- Loki: find recent log line containing a `trace_id`
- Prometheus: confirm recent samples in your key histograms

---

## docs/features/otel_tracing/feature.md

### What this feature adds
- OpenTelemetry tracing with **frontend-origin** trace creation and context propagation.
- Logs correlated with traces via `trace_id`.
- Metrics correlated with traces via **exemplars**.
- A Makefile-driven demo harness that reliably generates:
  - healthy signal
  - frontend latency issue
  - backend choking issue
  - dependency outage (Qdrant down)

### How to run the demo
- `make demo-verify` *(recommended before presenting)*
- `make demo-healthy-trace-signal`
- `make demo-frontend-latency-issue-trace-signal`
- `make demo-server-chocking-trace-signal`
- `make demo-qdrant-down-trace-signal`
- `make demo-reset` *(recommended after any scenario)*

### How to observe (runbook)
- Grafana dashboards:
  - “Demo Overview” (latency p95/p99, error rate, log volume)
- Grafana Explore:
  - Metrics: click exemplar dot → jump to trace
  - Logs: filter logs for the scenario, click `trace_id` → jump to trace
- Tempo:
  - search by service name and operation

### Troubleshooting quick hits
- No traces: check exporter endpoint env vars, Alloy OTLP receiver ports, and Tempo datasource.
- No `trace_id` in logs: confirm log formatter is injecting trace context.
- No exemplars: ensure exemplar support is enabled and you’re attaching them to histograms in code.

---

## docs/features/otel_tracing/changelog.md (optional)

### 2026-01-28
- Added OTEL tracing scaffold + demo harness including Qdrant outage scenario.

---

## End-of-work repo updates (required by scaffold standard)
When the feature is implemented, update:
- `ROADMAP.md` — add this feature and status
- `README.md` — add “How to run observability demo” section
- Any existing feature Change Log section + any global changelog file (if present)
