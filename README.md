# BookClub MVP — Local POC

## 🧠 One-liner

> An internal tool that turns technical PDFs into flashcards and spaced-repetition decks — powered by LLM + retrieval — to help engineers retain and apply what they read.

A minimal stack to build the PDF → Flashcards → SRS loop with optional Q&A. This stack provides Grafana/Prometheus/Loki locally using docker and docker-compose.

## 0) Prereqs
- Docker & Docker Compose
- Python >=3.11
- Grafana, Loki, Prometheus, Tempo, Qdrant, Alloy

## 1) Clone & Configure
```bash
git clone <repo>
cd <repo>
cp .env.example .env
# add your keys
```

## 2) Bring up infra (Qdrant + observability)
```bash
docker compose up -d qdrant loki promtail prometheus
```


## 3) Build & run the backend stub
```bash
docker compose up -d --build app
curl localhost:8000/healthz
```

## 4) Wire Grafana
- Add **Prometheus** datasource: `http://localhost:9090`
- Add **Loki** datasource: `http://localhost:3100`
- Import dashboard JSON from `observability/dashboards/` (optional)

## 5) Acceptance checks
- Prometheus shows `bookclub_requests_total` increasing after hitting `/`
- Loki shows logs from `bookclub-app` container
- Qdrant UI/API reachable at `http://localhost:6333`

## 6) Roadmap
### Phase 1: Observability
- [x] Send dev logs to Loki — logs from both app and development environment visible
- [x] Send function execution timings as Prometheus metrics
- [x] Optional: send test execution time metrics to Prometheus (via Pushgateway)
- [ ] Add Tempo service and Grafana Tempo datasource
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

### The definition of Done for phase 1:
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

### Phase 2: Backend
- [x] Implement basic REST Server, using FastAPI with the following enpoints:
  - `/metrics`
  - `/health`
  - `/ingest`
  - `/generate_flashcards`
  - `/srs`
  - `/anki_export`
    I want those endpoints to work on separate threads so that the main thread can continue to serve other requests and multiple calls can be served in the same time.
- [ ] Implement asynchronisity to the calls of endpoints, test, measure and verify.

### The definition of Done for phase 2:
  - The Backend functionality:
    - [ ] I'm able to get the metrics from the server and see them in Grafana.
    - [ ] I'm able to compare the tests between branches/commits of the repo in Grafana
    - [ ] I'm able to see the change of execution latency, duration and error rate of calls in time for all tests, differentiating between the branches/commits, test types and test files of the repo in Grafana.
  - The backend observability:
    - [ ] I'm able to see function execution time for endpoints each branch/commit of the repo in Grafana
    - [ ] I'm able to compare the function execution time between branches/commits of the repo in Grafana
    - [ ] I'm able to see the change of function execution time in time for all functions, differentiating between the branches/commits, function types and function files of the repo in Grafana.
    - I'm measuring following metrics of the server:
      - [ ] Request rate (RPS):
        How many HTTP requests server handles per second/minute/hour/24h.
      - [ ] In flight requests:
        How many HTTP requests server handles at this time.
      - [ ] Request latency (end-to-end):
        How long it takes for the server to handle a request, p50, p95/p99 tail per endpoint.
      - [ ] Dependency latency:
        Time spend calling DB, p50, p95/p99 tail per endpoint.
      - [ ] Request error rate:
        How many HTTP requests is returned as errors in second/minute/hour/24h.
      - [ ] 4xx breakdown:
        Split between 400, 401/403/404/409/422/429/4xx.
      - [ ] 5xx breakdown:
        Split between 500, 502/503/504/5xx.

### Phase 2.5: Experimentation:
- [ ] Make sure that the previous sessions is clearly tagged in and saved, make a backup.
- [ ] Implement the lessons learned from this video: https://www.youtube.com/watch?v=HTSK6eRwyGM
- [ ] Make a dashboard with frozen data that shows time execution before and after implementation of the lessons learned above.


### Phase 3: CI/CD
- [ ] Write initial CI/CD:
  - [ ] Make all test not related to observability run on commit & push and PR's.
  - [ ] Make all test related to observability run on commit & push and PR's.
  - [ ] Make GH Actions tag the commit with label "passing tests" if all tests pass.
  - [ ] Make CI/CD feedback to localhost.
  - [ ] Make GitHUb actions push this commit/PR metadata [branch from, commit hash, commit message, author, labels] so that I can see them in Grafana as time series.

### Definition of Done for phase 3:
  - The CI/CD runs all the tests pn p

### Phase 4: LLMs
- [ ] Modularise LLM provider:
  - [ ] Get one local LLM provider that I'll be able to query from app run in docker container - Ollama?
  - [ ] Get one remote LLM provider that I'll be able to query from app run in docker container - Free tier? - OpenAI? Gemini?
- [ ] Implement `ingest` (parse → chunk → embed → upsert to Qdrant) - called by the API endpoint.
- [ ] Implement `generate_flashcards` (retrieval + LLM prompt + JSON output) - called by the API endpoint.
- [ ] Implement `srs` and minimal CLI to review 5 cards - called by the API endpoint.
- [ ] Implement `anki_export` (CSV first) - called by the API endpoint.
- [ ] Add `/metrics` counters for ingestion time, chunks, cards_generated and quickly visible devided by sessions and books.
- [ ] Create `docs/demo_script.md` (3‑minute flow).

### Phase 5: Observability with Grafana, Deep Dive
- [ ] Provisioning as code: datasources, dashboards, alerting (YAML under `observability/grafana/provisioning/`)
- [ ] Recording rules and performance: Prometheus recording rules; ruler/compactor tuning
- [ ] Dashboard excellence: variables, transformations, drilldowns, links, UIDs, owners, folders
- [ ] SLOs and error budgets: burn‑rate alerts, SLI panels, runbooks
- [ ] Incident response: notification policies, grouping, silences, basic OnCall integration (optional)
- [ ] Label cardinality and cost controls: metrics/logs label strategy, Loki/Tempo retention
- [ ] Security & RBAC: folders, teams, roles, secrets handling
- [ ] Scaling notes (optional): Mimir/Loki/Tempo high‑level architecture and limits

### The definition of Done for phase 5:
- [ ] Datasources, dashboards, and alerting are provisioned as code; no manual drift
- [ ] Key dashboards follow standards: owner, UID, folder, variables, links, and on‑panel runbook links
- [ ] At least one SLO with burn‑rate alerts is live and documented; runbook exists and is linked
- [ ] Critical alert noise reduced via grouping/routing/silences; test plan demonstrates expected behaviour
- [ ] Recording rules reduce dashboard query latency on hot paths without losing fidelity
- [ ] Retention and label cardinality policies documented and applied (Prometheus, Loki, Tempo)
- [ ] Access controls (folders/teams) applied according to documented policy

## 7) Troubleshooting
- If models are local (Ollama), ensure `OLLAMA_HOST` is reachable from container (use `host.docker.internal` on mac/win, or host IP on linux).
- If Prometheus/Loki already exist elsewhere, **comment out** those services in `docker-compose.yml` and point Grafana at theg
 existing ones.

## 8) Documentation

### Observability Documentation

- **[Execution Timings](docs/execution_timings.md)** - Function performance tracking with `@track_timing` decorator.
  - Automatic metrics for execution time, call counts, and error rates.
  - Supports sync/async functions, Gunicorn multiprocess mode, and trace exemplars.
- **[Execution Timings Verification](docs/execution_timings_verification.md)** - Integration guide and troubleshooting.
  - Step-by-step setup, testing workflows, and Grafana dashboard examples.

- **[Test Metrics](docs/test_metrics.md)** - pytest test execution metrics via Pushgateway.
  - Batch collection, cleanup modes (before, after, both, none).
  - Per-test duration tracking with custom labels and tags.
- **[Test Metrics Verification](docs/test_metrics_verification.md)** - Pipeline verification and CI/CD integration.
  - Make commands for validation, cleanup behavior tests.

### Quick Links

```bash
# Function timing decorator
@track_timing(namespace="api")
async def my_endpoint():
    pass

# Test metrics (in pytest)
pytest --pushgw=http://localhost:9091 --prom-cleanup=after

# Verify pipelines
make verify-test-metrics
make test-cleanup-behavior
```

## Optional: `observability/dashboards/` (placeholder)
- Add exported Grafana dashboard JSON here once you’ve built the first panels:
  - Ingestion duration (histogram)
  - Chunks created per PDF
  - Cards generated per session
  - Q&A latency (if implemented)

# Lessons learned:
## Docker and sudo:
- If you are using sudo to run docker commands, you need rnable passwordless sudo for the user runnig docker commands. Otherwise, tests that rely on connections or are testing conenctions between dockerized containers and other docker related commands will fail with a permission error.

You can add the user to the docker group with the following command: `sudo usermod -aG docker $USER` then restart your terminal or change into docker group with `newgrp docker` - verify with `docker ps`.

To configure passwordless sudo <sic!> < Use with caution! >, add the following line to the sudoers file: `your_username ALL=(ALL) NOPASSWD: ALL` - verify with `sudo -l`. To open sudoers file for docker, use `sudo visudo -f /etc/sudoers.d/docker`.

This is interesting find that there is passwordless sudo. It's like a whitelist for applications to run as root, something like checking "run as administrator" on windows but without the hassle of clicking the button.

## Testing Loki:
When testing logs processing. Make sure that your app generates at least some logs xD.

## Prcedence of env vars:
First of all command `docker compose config` shows solved configuration file with all defaults elements and fed environment variables.

If Docker Compose attributes are written to first search for a variable in the environment, then the top `.env` file values will have precedence. e.g "`TOP_ENV_FILE:  ${TOP_ENV_FILE:-DOCKER_COMPOSE_DIRECT}`".

Also docker compose can feed singular environment variables via `environment` attribute to the container or target .env file that is mounted to the container e.g "`env_file: - ./src/book_club/server/.env`".

Precedense of solving environment variables (from highest to lowest) based on docker compose docs:
- environment: section in docker-compose.yml
- Shell environment variables (exported in the host)
- .env file in the project root
- env_file: attribute
- Dockerfile ENV directives

https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/

## Why -the fuck- am i getting the douplicated metrics values?
I think it's because the metrics are being collected by the server and by the gunicorn worker, and I don't know how to fix it.

## Reset password in Grafana:
To reset a password for Grafana admin - once youve set one yourself - you need to get into grafana's docker shell via 'docker exec -it grafana sh' and use the following command `grafana-cli admin reset-admin-password '<new-password>'`

You can initialise the grafana with a set up password by providing a env variable of `GF_SECURITY_ADMIN_PASSWORD` but this will not change the set passwords.

## The dependency graph in UV
UV as a depndency tree display option for project `uv tree` simillar to `poetry show --tree` or `pipenv graph`. THats nice. Using pip you had to install additional dependency `pipdeptree` which kinda was against the point.
Also same for the npm it has `npm ls` but be cautious it has the `--depth` parameter to limit the frontend depndencies. Wow, frontend really has a problem.
For Rust its `cargo tree`.
For Ubuntu its external, not installed by default, but official package `apt-rdepends`.
For Arch its 'pactree' and its inastalled by default.