# BookClub MVP — Local POC

## 🧠 One-liner

> An internal tool that turns technical PDFs into flashcards and spaced-repetition decks — powered by LLM + retrieval — to help engineers retain and apply what they read.

A minimal stack to build the PDF → Flashcards → SRS loop with optional Q&A. This stack provides Grafana/Prometheus/Loki locally using docker and docker-compose.

## 0) Prereqs
- Docker & Docker Compose
- Python >=3.11
- Grafana reachable

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
- Add **Prometheus** datasource: `http://<this-host>:9090`
- Add **Loki** datasource: `http://<this-host>:3100`
- Import dashboard JSON from `observability/dashboards/` (optional)

## 5) Acceptance checks
- Prometheus shows `bookclub_requests_total` increasing after hitting `/`
- Loki shows logs from `bookclub-app` container
- Qdrant UI/API reachable at `http://localhost:6333`

## 6) Next steps (MVP tasks)
- [ ] Implement `ingest.py` (parse → chunk → embed → upsert to Qdrant)
- [ ] Implement `generate_flashcards.py` (retrieval + LLM prompt + JSON output)
- [ ] Implement `srs.py` and minimal CLI to review 5 cards
- [ ] Implement `anki_export.py` (CSV first)
- [ ] Add `/metrics` counters for ingestion time, chunks, cards_generated
- [ ] Create `docs/demo_script.md` (3‑minute flow)

## 7) Troubleshooting
- If models are local (Ollama), ensure `OLLAMA_HOST` is reachable from container (use `host.docker.internal` on mac/win, or host IP on linux).
- If Prometheus/Loki already exist elsewhere, **comment out** those services in `docker-compose.yml` and point Grafana at the existing ones.

## Optional: `observability/dashboards/` (placeholder)
- Add exported Grafana dashboard JSON here once you’ve built the first panels:
  - Ingestion duration (histogram)
  - Chunks created per PDF
  - Cards generated per session
  - Q&A latency (if implemented)

