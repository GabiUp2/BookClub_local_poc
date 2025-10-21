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
- [ ] Implement minimal observability stack (Prometheus + Grafana + Loki + Tempo)
  - [x] Send dev logs to Loki - loks from both app and developemnt environement are there
  - [ ] Send function time execution to metrics to Prometheus
  - [ ] Optional: send tests execution time as metrics to Prometheus with granularity per test, with labels of files, pytest tags, etc.
  - [ ] Send little traces to Tempo - What's a good small trace to send from the app?
- [ ] Implement basic REST Server, using FastAPI with the following enpoints:
  - `/metrics`
  - `/health`
  - `/ingest`
  - `/generate_flashcards`
  - `/srs`
  - `/anki_export`
    I want those endpoints to work on separate threads so that the main thread can continue to serve other requests and multiple calls can be served in the same time.
- [ ] Modularise LLM provider:
  - [ ] Get one local LLM provider that I'll be able to query from app run in docker container - Ollama?
  - [ ] Get one remote LLM provider that I'll be able to query from app run in docker container - Free tier? - OpenAI? Gemini?
- [ ] Implement `ingest` (parse → chunk → embed → upsert to Qdrant) - called by the API endpoint
- [ ] Implement `generate_flashcards` (retrieval + LLM prompt + JSON output) - called by the API endpoint
- [ ] Implement `srs` and minimal CLI to review 5 cards - called by the API endpoint
- [ ] Implement `anki_export` (CSV first) - called by the API endpoint
- [ ] Add `/metrics` counters for ingestion time, chunks, cards_generated and quickly visible devided by sessions and books
- [ ] Create `docs/demo_script.md` (3‑minute flow)
- [ ] Add optional observability dashboards from section below
- [ ] Optional: Python observability deep dive
  - [ ] Optional: Add decorator for timing methods and sending them as metrics through Prometheus into Grafana
  - [ ] Optional: Add a way to add test times as metrics through Prometheus into Grafana
  - [ ] Optional: Add parser for tool for parsing memory profiling output into Grafana as a panel
  - [ ] Optional: Add parser for tool for parsing CPU profiling output into Grafana as a panel
  - [ ] Optional: Add parser for tool for parsing GC profiling output into Grafana as a panel
  - [ ] Optional: Add parser for tool for parsing heap profiling output into Grafana as a panel
  - [ ] Optional: Add parser for tool for parsing thread profiling output into Grafana as a panel
- [ ] Optional: Add Mimir as storage for metrics

## 7) Troubleshooting
- If models are local (Ollama), ensure `OLLAMA_HOST` is reachable from container (use `host.docker.internal` on mac/win, or host IP on linux).
- If Prometheus/Loki already exist elsewhere, **comment out** those services in `docker-compose.yml` and point Grafana at theg
 existing ones.

## Optional: `observability/dashboards/` (placeholder)
- Add exported Grafana dashboard JSON here once you’ve built the first panels:
  - Ingestion duration (histogram)
  - Chunks created per PDF
  - Cards generated per session
  - Q&A latency (if implemented)

