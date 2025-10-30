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

## 6) Next steps (MVP tasks)
### Phase 1: Observability
- [ ] Implement minimal observability stack (Prometheus + Grafana + Loki + Tempo)
  - [x] Send dev logs to Loki - loks from both app and developemnt environement are there
  - [x] Send function times of execution as metrics to Prometheus
  - [x] Optional: send tests execution time as metrics to Prometheus with granularity per test, with labels of files and pytest tags - use pushgate?
  - [ ] Send little traces to Tempo - What's a good small trace to send from the app or from server?

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

### Phase 3: CI/CD
- [ ] Write initial CI/CD:
  - [ ] Make all test not related to observability run on commit & push and PR's.
  - [ ] Make all test related to observability run on commit & push and PR's.
  - [ ] Make GH Actions tag the commit with label "passing tests" if all tests pass.
  - [ ] Make CI/CD feedback to localhost.
  - [ ] Make GitHUb actions push this commit/PR metadata [branch from, commit hash, commit message, author, labels] so that I can see them in Grafana as time series.

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

### Phase 5: Observability 2
- [ ] Add optional observability dashboards from section below.
- [ ] Optional: Python observability deep dive.
  - [ ] Optional: Add parser for tool for parsing memory profiling output into Grafana as a panel.
  - [ ] Optional: Add parser for tool for parsing CPU profiling output into Grafana as a panel.
  - [ ] Optional: Add parser for tool for parsing GC profiling output into Grafana as a panel.
  - [ ] Optional: Add parser for tool for parsing heap profiling output into Grafana as a panel.
  - [ ] Optional: Add parser for tool for parsing thread profiling output into Grafana as a panel.
- [ ] Add Mimir as storage for metrics - just to see how to set it up.
- [ ] Solution Version 1:Add Proxy to pushgateway with auto delete upon completing filled metrics call.
- [ ] Solution Version 2: Add Expose server endpoints for tests run on it? O_o?

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
