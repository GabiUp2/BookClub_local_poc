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

## 6) Observability demo (OTEL tracing)

OTEL tracing is implemented: frontend and backend emit traces; logs and metrics correlate via `trace_id` and exemplars.

- **Quick check**: `make demo-verify` (smoke-checks Tempo, Loki, Prometheus).
- **Generate demo signal**: `make demo-healthy-trace-signal` then open Grafana (Tempo/Loki/Prometheus).
- **Demo scenarios**: `make demo-frontend-latency-issue-trace-signal`, `make demo-server-chocking-trace-signal`, `make demo-qdrant-down-trace-signal`; `make demo-reset` to restore.

See **[OTEL Tracing feature doc](docs/features/otel_tracing/feature.md)** for configuration, API, and runbook.

## 7) Current Tasks

### 1) Remaining observability

- Add git commit/branch to metrics and log labels.
- Add basic alerting: p95 latency per endpoint; error‑rate and ERROR‑log spike.

### 2) MVP cut (backend + observability)

- Backend endpoints ready: `/metrics`, `/health`, `/ingest`, `/generate_flashcards`, `/srs`, `/anki_export`.
- Implement and verify async where beneficial; measure latency and error‑rate.
- Acceptance checks in Grafana: request rate, latency distributions (p50/p95/p99), in‑flight, error‑rate.

### 3) Post‑MVP (next up)

- CI/CD: run tests on push/PR; tag passing commits; surface build metadata to Grafana.
- LLM workflow: ingest → chunk → embed (Qdrant); flashcard generation; minimal SRS; Anki export.
- Observability deep‑dive: provisioning as code; SLOs; recording rules; RBAC and retention.

See ROADMAP.md for the full, granular task list grouped by area.

## 8) Troubleshooting

- If models are local (Ollama), ensure `OLLAMA_HOST` is reachable from container (use `host.docker.internal` on mac/win, or host IP on linux).
- If Prometheus/Loki already exist elsewhere, **comment out** those services in `docker-compose.yml` and point Grafana at the existing ones.
- **No traces in Grafana / TraceQL "0 series"**: Rebuild and recreate the backend so OTEL runs in each Gunicorn worker (`docker compose build bookclub-preprocessing-server && docker compose up -d --force-recreate bookclub-preprocessing-server`), then run `make demo-healthy-trace-signal` and wait 15s. In Grafana Explore (Tempo) use the **Search** tab and filter by tag `service.name` = `bookclub-preprocessing-server`. See [OTEL Tracing feature doc](docs/features/otel_tracing/feature.md) for full runbook.

## 9) Documentation

### Observability Documentation

- **[OTEL Tracing](docs/features/otel_tracing/feature.md)** - End-to-end tracing (frontend → backend), log/metric correlation, demo harness (`make demo-verify`, `make demo-healthy-trace-signal`, etc.).
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

# Feature backlog:
## Vector Databases to consider:
* PGVector: Open-source vector similarity search for PostgreSQL
* sqlite-vec: Open-source vector similarity search for SQLite
* LanceDB: Local-first, simple setup, small–medium scale
* Weaviate: Full-featured, GraphQL API, complex schema
* QDrant

## Retrieval performance augementation
* Hierarchical navigable small world - https://en.wikipedia.org/wiki/Hierarchical_navigable_small_world
* Inverted File Flat Vector Indexes - https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/understand-inverted-file-flat-vector-indexes.html
* Locality-sensitive hashing - https://en.wikipedia.org/wiki/Locality-sensitive_hashing
* Precision vs Recall measures - https://en.wikipedia.org/wiki/Precision_and_recall

## Chunking
* Test overlaps between chunks, assume local optimum at ~20%


# Possible confusions in code:
## interchangibility of term "server" and "preprocessing server".
The later term was introduced later in development when there was the need to distnguish one server from another server, already then there were more than 2k+ uses of term server in codebase and i just didnt had heart to go through each one of them. I've made it so the tests would run and make files target were clear, then left it there.
 So if it is not clear what server the term "server" relates to, the "preprocessing_server" might be a good shoot to start with.

# Lessons learned

## Docker and sudo

- If you are using sudo to run docker commands, you need enable passwordless sudo for the user running docker commands. Otherwise, tests that rely on connections or are testing connections between dockerized containers and other docker related commands will fail with a permission error.

You can add the user to the docker group with the following command: `sudo usermod -aG docker $USER` then restart your terminal or change into docker group with `newgrp docker` - verify with `docker ps`.

To configure passwordless sudo <sic!> < Use with caution! >, add the following line to the sudoers file: `your_username ALL=(ALL) NOPASSWD: ALL` - verify with `sudo -l`. To open sudoers file for docker, use `sudo visudo -f /etc/sudoers.d/docker`.

This is interesting find that there is passwordless sudo. It's like a whitelist for applications to run as root, something like checking "run as administrator" on windows but without the hassle of clicking the button.

## Testing Loki

When testing logs processing. Make sure that your app generates at least some logs xD.

## Precedence of env vars

First of all command `docker compose config` shows solved configuration file with all defaults elements and fed environment variables.

If Docker Compose attributes are written to first search for a variable in the environment, then the top `.env` file values will have precedence. e.g "`TOP_ENV_FILE:  ${TOP_ENV_FILE:-DOCKER_COMPOSE_DIRECT}`".

Also docker compose can feed singular environment variables via `environment` attribute to the container or target .env file that is mounted to the container e.g "`env_file: - ./src/book_club/preprocessing_server/.env`".

Precedence of solving environment variables (from highest to lowest) based on docker compose docs:

- environment: section in docker-compose.yml
- Shell environment variables (exported in the host)
- .env file in the project root
- env_file: attribute
- Dockerfile ENV directives

<https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/>

## Why -the fuck- am i getting the douplicated metrics values?

I think it's because the metrics are being collected by the server and by the gunicorn worker, and I don't know how to fix it, yet.

## Reset password in Grafana

To reset a password for Grafana admin - once you've set one yourself - you need to get into grafana's docker shell via 'docker exec -it grafana sh' and use the following command `grafana cli admin reset-admin-password '<new-password>'`

You can initialise the grafana with a set up password by providing a env variable of `GF_SECURITY_ADMIN_PASSWORD` but this will not change the set passwords.

## The dependency graph in UV

UV as a dependency tree display option for project `uv tree` similar to `poetry show --tree` or `pipenv graph`. Thats nice. Using pip you had to install additional dependency `pipdeptree` which kinda was against the point.
Also same for the npm it has `npm ls` but be cautious it has the `--depth` parameter to limit the frontend depndencies. Wow, frontend really has a problem.
For Rust its `cargo tree`.
For Ubuntu its external, not installed by default, but official package `apt-rdepends`.
For Arch its 'pactree' and its installed by default.

## If you don't know how big project will become - DO NOT USE GENERAL NAMES FOR IT'S MODULES!
You don't need specificity untill the project gets big and once it gets big you need to propagate changes to many places in the codebase. I just spend 2,5 hour becouse I needed to change the name of the "server" to "preprocessing-server", and more features you have more stuff you need to correct, form module imports to observability metrics labels in dashboard. I think it would be faster if i had name the server something like "server_A" or even "server_1", then search would be much easier as term "server" can be used in internal logic where it is valid and shoud have stayed.
