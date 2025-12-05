# Roadmap

This file contains the granular task lists grouped by area. The README contains a concise, prioritised “Current Tasks” section.

## Observability (OTEL)

- [x] Send dev logs to Loki — logs from both app and development environment visible
- [x] Send function execution timings as Prometheus metrics
- [x] Optional: send test execution time metrics to Prometheus (via Pushgateway)
- [x] Add Tempo service and Grafana Tempo datasource
- [ ] Enable OTEL: instrument FastAPI/app with OpenTelemetry SDK
  - [ ] Set OTEL resource attrs: `service.name`, `deployment.environment`, `git.commit`, `git.branch`
  - [ ] Export traces via Alloy OTLP to Tempo
- [ ] Correlate signals:
  - [ ] Include `trace_id` in logs (Loki) and enable trace exemplars on latency metrics
  - [ ] Grafana Explore: pivot metrics ↔ logs ↔ traces for a single request
- [ ] Add git commit and branch to metrics and logs labels
- [ ] Add basic alerting:
  - [ ] p95 latency per endpoint (Prometheus)
  - [ ] Error rate (Prometheus) and ERROR log spike (Loki)

### Definition of Done — Observability

- The Observability — tests:
  - [ ] I can see test execution by branch/commit in Grafana and compare across branches/commits
  - [ ] I can see the trend of per‑test duration over time, filtered by branch/commit/test file/tags
- The Observability — function execution time (API):
  - [ ] I can see endpoint execution time distributions (p50/p95/p99), request rate, in‑flight, error rate
  - [ ] I can compare these across branches/commits and over time
- The Observability — traces and correlations:
  - [ ] Tempo receives traces from the app; I can view spans for a request (including DB/external calls)
  - [ ] Metrics panels show trace exemplars; logs include `trace_id` and link to traces
  - [ ] From a metric panel I can pivot to related logs and the corresponding trace
- The Observability — alerting and operations:
  - [ ] Alert rules exist for high error rate and high p95 latency, with a working contact point
  - [ ] Acknowledge/silence flow verified in Grafana Alerting

## Backend (MVP)

- [x] Implement basic REST Server, using FastAPI with the following endpoints:
  - `/metrics`
  - `/health`
  - `/ingest`
  - `/generate_flashcards`
  - `/srs`
  - `/anki_export`
    I want those endpoints to work on separate threads so that the main thread can continue to serve other requests and multiple calls can be served in the same time.
- [ ] Implement asynchronisity to the calls of endpoints, test, measure and verify.

### Definition of Done — Backend

- The Backend functionality:
  - [ ] I'm able to get the metrics from the server and see them in Grafana.
  - [ ] I'm able to compare the tests between branches/commits of the repo in Grafana
  - [ ] I'm able to see the change of execution latency, duration and error rate of calls in time for all tests, differentiating between the branches/commits, test types and test files of the repo in Grafana.
- The backend observability:
  - [ ] I'm able to see function execution time for endpoints each branch/commit of the repo in Grafana
  - [ ] I'm able to compare the function execution time between branches/commits of the repo in Grafana
  - [ ] I'm able to see the change of function execution time in time for all functions, differentiating between the branches/commits, function types and function files of the repo in Grafana.
  - I'm measuring following metrics of the server:
    - [ ] Request rate (RPS): How many HTTP requests server handles per second/minute/hour/24h.
    - [ ] In flight requests: How many HTTP requests server handles at this time.
    - [ ] Request latency (end-to-end): How long it takes for the server to handle a request, p50, p95/p99 tail per endpoint.
    - [ ] Dependency latency: Time spend calling DB, p50, p95/p99 tail per endpoint.
    - [ ] Request error rate: How many HTTP requests is returned as errors in second/minute/hour/24h.
    - [ ] 4xx breakdown: Split between 400, 401/403/404/409/422/429/4xx.
    - [ ] 5xx breakdown: Split between 500, 502/503/504/5xx.

## Experimentation

- [ ] Make sure that the previous sessions is clearly tagged in and saved, make a backup.
- [ ] Implement the lessons learned from this video: <https://www.youtube.com/watch?v=HTSK6eRwyGM>
- [ ] Make a dashboard with frozen data that shows time execution before and after implementation of the lessons learned above.

## CI/CD

- [ ] Write initial CI/CD:
  - [ ] Make all test not related to observability run on commit & push and PR's.
  - [ ] Make all test related to observability run on commit & push and PR's.
  - [ ] Make GH Actions tag the commit with label "passing tests" if all tests pass.
  - [ ] Make CI/CD feedback to localhost.
  - [ ] Make GitHUb actions push this commit/PR metadata [branch from, commit hash, commit message, author, labels] so that I can see them in Grafana as time series.

### Definition of Done — CI/CD

- [ ] The CI/CD runs all the tests pn p

## LLMs

- [ ] Modularise LLM provider:
  - [ ] Get one local LLM provider that I'll be able to query from app run in docker container - Ollama?
  - [ ] Get one remote LLM provider that I'll be able to query from app run in docker container - Free tier? - OpenAI? Gemini?
- [ ] Implement `ingest` (parse → chunk → embed → upsert to Qdrant) - called by the API endpoint.
- [ ] Implement `generate_flashcards` (retrieval + LLM prompt + JSON output) - called by the API endpoint.
- [ ] Implement `srs` and minimal CLI to review 5 cards - called by the API endpoint.
- [ ] Implement `anki_export` (CSV first) - called by the API endpoint.
- [ ] Add `/metrics` counters for ingestion time, chunks, cards_generated and quickly visible devided by sessions and books.
- [ ] Create `docs/demo_script.md` (3‑minute flow).

## Observability Deep Dive

- [ ] Provisioning as code: datasources, dashboards, alerting (YAML under `observability/grafana/provisioning/`)
- [ ] Recording rules and performance: Prometheus recording rules; ruler/compactor tuning
- [ ] Dashboard excellence: variables, transformations, drilldowns, links, UIDs, owners, folders
- [ ] SLOs and error budgets: burn‑rate alerts, SLI panels, runbooks
- [ ] Incident response: notification policies, grouping, silences, basic OnCall integration (optional)
- [ ] Label cardinality and cost controls: metrics/logs label strategy, Loki/Tempo retention
- [ ] Security & RBAC: folders, teams, roles, secrets handling
- [ ] Scaling notes (optional): Mimir/Loki/Tempo high‑level architecture and limits

### Definition of Done — Observability Deep Dive

- [ ] Datasources, dashboards, and alerting are provisioned as code; no manual drift
- [ ] Key dashboards follow standards: owner, UID, folder, variables, links, and on‑panel runbook links
- [ ] At least one SLO with burn‑rate alerts is live and documented; runbook exists and is linked
- [ ] Critical alert noise reduced via grouping/routing/silences; test plan demonstrates expected behaviour
- [ ] Recording rules reduce dashboard query latency on hot paths without losing fidelity
- [ ] Retention and label cardinality policies documented and applied (Prometheus, Loki, Tempo)
- [ ] Access controls (folders/teams) applied according to documented policy
