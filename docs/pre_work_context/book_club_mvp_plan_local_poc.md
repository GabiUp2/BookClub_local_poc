# Book Club — MVP Plan (Local POC)

**Owner:** You  
**Mode:** Single-developer POC on local machine  
**Infra:** Local filesystem for storage, your OpenAI (or compatible) API tokens, Grafana on home server for observability  
**Target Duration:** 2–3 weeks, part‑time  
**Purpose of this Doc:** This is an execution-ready plan with explicit success criteria per step so other LLMs can act as your project manager or pair‑programmer.

---

## 0) Hard Constraints & Non‑Goals

**Constraints**
- Runs entirely on **your machine** (no cloud dependencies beyond model API usage).
- **Local storage**: PDFs, embeddings, vector index, and SQLite DB on disk.
- **Observability**: Export logs/metrics/traces to your **Grafana** via Grafana Agent/OTLP.

**Non‑Goals (for POC)**
- EPUB/MOBI support (PDF only).
- Team/collaboration features, SSO, RBAC.
- Advanced privacy controls beyond local token handling.
- Fancy UI/UX; aim for minimal, fast, and reliable.

---

## 1) MVP Outcome (Definition of Done)

Ship a local tool that:
1. **Ingests a PDF**, chunks it, embeds chunks, and builds a local vector index.
2. Supports **retrieval‑augmented Q&A** with **citations** (chunk IDs + text snippets).
3. **Generates 20–30 flashcards** (basic & cloze) from selected chapters/sections.
4. Provides a **spaced‑repetition review** loop (SM‑2) via a minimal web UI.
5. Emits **OpenTelemetry traces/metrics/logs** visible in your Grafana dashboards.
6. Persists everything locally (filesystem + SQLite) and can **export Anki‑compatible** decks (.csv or .apkg via genanki).

**Global Success Criteria**
- **Time‑to‑first‑value:** < **3 minutes** from dropping a PDF to first 10 flashcards visible.
- **Answer grounding:** ≥ **85%** of Q&A responses include the correct citation chunk(s) on manual spot‑check of 20 queries.
- **Flashcard quality:** On a 20‑card sample, ≥ **70%** are clear, atomic, and unambiguous.
- **Stability:** No crashes in a 30‑minute exploration session; graceful error messages.
- **Observability:** At least 1 dashboard panel each for **QPS**, **latency p95**, **token cost estimate**, and **flashcards generated/day**.

---

## 2) Architecture (Local POC)

**Process**: Single FastAPI app (backend) + ultra‑light React/HTMX frontend (or CLI fallback).  
**Storage**:
- **Filesystem**: `/data/books`, `/data/chunks`, `/data/index` (FAISS), `/data/exports`.
- **DB**: SQLite (`/data/app.db`) for books, chunks metadata, cards, SRS reviews.
- **Vector Index**: FAISS (flat L2 or IVF). Optional BM25 via `rank-bm25` for hybrid later.

**Models**:
- **Embeddings**: OpenAI `text-embedding-3-small` (fast, cheap) or local `all-MiniLM-L6-v2` via sentence-transformers.
- **LLM**: OpenAI GPT‑4o‑mini (or any compatible via LiteLLM). Keep provider behind an interface.

**Observability**:
- Python `opentelemetry-sdk` + `opentelemetry-instrumentation-fastapi`.
- Exporter: OTLP to **Grafana Agent** → Grafana (Tempo for traces, Prometheus for metrics, Loki for logs if configured).

---

## 3) Project Structure (Scaffold)

```
bookclub/
  app.py                  # FastAPI entrypoint
  settings.py             # Config/env handling
  domain/
    ingest.py             # PDF parsing + chunking
    embed.py              # Embedding client abstraction
    index.py              # FAISS index ops (build/search)
    retrieve.py           # Top-k retrieval + scoring
    qa.py                 # RAG answer w/ citations
    cards.py              # Flashcard generation + schema
    srs.py                # SM-2 scheduling
  adapters/
    openai_client.py      # LLM + Embeddings via OpenAI/LiteLLM
    local_embedder.py     # Optional local embeddings
    telemetry.py          # OTEL setup, log helpers
    storage.py            # SQLite + file ops
  ui/
    static/               # minimal CSS/JS
    templates/            # Jinja/HTMX or React build
  scripts/
    build_index.py        # CLI helpers
    export_anki.py        # CSV/.apkg exporter
  tests/
    test_chunking.py
    test_retrieval.py
    test_cards.py
  data/
    books/                # PDFs
    index/                # FAISS files
    exports/              # Anki
    app.db                # SQLite
  Makefile
  requirements.txt (or pyproject.toml)
  README.md
  .env.example
```

---

## 4) Step‑by‑Step Plan (with Success Criteria)

### Step 1 — Environment & Telemetry
**Goal:** Reliable local run with observability from day one.

**Tasks**
- Create virtualenv; install FastAPI, Uvicorn, FAISS, PyMuPDF, sentence-transformers (optional), OpenAI/LiteLLM, pydantic, opentelemetry packages, genanki (optional).
- Implement `settings.py` to read `.env` (API keys, OTLP endpoint, data dirs).
- Add `adapters/telemetry.py` to init OTEL (service.name=`bookclub-poc`, resource attrs: git_sha, env=local).
- Wire middleware to trace requests; add custom spans for **ingest**, **embed.batch**, **index.build**, **rag.answer**, **cards.generate**, **srs.review**.

**Success**
- `make run` starts API; hitting `/health` shows OK.
- Grafana shows inbound traces for `/ingest` and metrics counters (requests_total) within 1 minute.

---

### Step 2 — PDF Ingestion & Chunking
**Goal:** Deterministic chunking pipeline.

**Tasks**
- Parse PDF with PyMuPDF; extract text + headings via font sizes/TOC if present.
- Heuristics: chunk by **heading or ~800–1200 tokens** with overlap 100.
- Persist: book record, chunk records (id, book_id, start_page, end_page, text, md5).
- Emit span events with chunk counts and token estimates.

**Success**
- Ingest a 200‑page technical PDF in **<60s**.
- **>95%** of chunk records have non‑empty text; total tokens within ±20% of estimate.

---

### Step 3 — Embeddings & Index Build
**Goal:** Fast, reproducible vector index creation.

**Tasks**
- Batch embed chunks (size 64–128, backoff, retry).
- Store embeddings on disk as FAISS index; map chunk_id → vector row.
- Record costs/time in metrics (`embedding_tokens_total`, `embedding_seconds`).

**Success**
- Index build completes without error; FAISS file persisted.
- Querying a sample sentence returns **semantically relevant** top‑k chunks (manual eye test on 10 prompts).

---

### Step 4 — Retrieval‑Augmented Q&A with Citations
**Goal:** Trustworthy answers or explicit “I don’t know”.

**Tasks**
- Implement retriever (top‑k=5) → prompt composer → LLM answerer.
- Prompt must **quote** snippet IDs; answer returns: `answer`, `citations: [{chunk_id, page, snippet}]`.
- Add guardrails: if max similarity < threshold, return "I don’t know — no relevant context found.".

**Success**
- On 20 test questions, ≥ **85%** have correct supporting snippets.
- Latency p95 **< 3s** for cached/small queries (excluding first‑time embedding).

---

### Step 5 — Flashcard Generation (Basic + Cloze)
**Goal:** Auto‑create study‑ready cards, grounded in text.

**Tasks**
- Implement `cards.generate(chunks|sections, n=30)` using LLM with a strict JSON schema: `{type: "basic"|"cloze", question, answer, source_chunk_id}`.
- Validate with pydantic; deduplicate by normalized question.
- Store in SQLite; expose via `/cards?book_id=` API.

**Success**
- For a single chapter, system generates **≥20** valid cards in **<90s**.
- Manual sample of 20 cards: **≥70%** pass clarity/atomicity; all have source links.

---

### Step 6 — SRS (SM‑2) & Minimal Review UI
**Goal:** Make learning sticky with minimal friction.

**Tasks**
- Implement SM‑2 fields per card: EF, interval, repetitions, due_date.
- Endpoint `/review/next?limit=10` returns due cards; `/review/submit` updates schedule given quality (0–5).
- UI: ultra‑light HTMX/Alpine (or small React) to show **one card at a time**, reveal answer, grade 0–5, next.

**Success**
- A user can complete a 10‑card session in **<5 minutes** without errors.
- Card due dates update correctly; subsequent calls return new queue.

---

### Step 7 — Anki Export & CLI Utilities
**Goal:** Ensure portability and habit continuity.

**Tasks**
- Export selected deck to **CSV** (min): `question,answer,tags,source`.
- Optional: `.apkg` via `genanki` with basic styling.
- Add CLI scripts: `scripts/build_index.py`, `scripts/export_anki.py`.

**Success**
- Import CSV into Anki; at least **95%** of cards render correctly on mobile.

---

### Step 8 — Polishing & Guardrails
**Goal:** Make the POC resilient and safe to demo.

**Tasks**
- Input validation, file type checks, size limits, streaming progress bars.
- Error pages with actionable next steps.
- Cost estimator: track prompt/embedding tokens and show **€ estimate/session**.
- Add content filter to avoid generating cards from tiny/boilerplate chunks.

**Success**
- 30‑minute exploratory session: **0 crashes**, **clear errors**, **cost panel visible**.

---

## 5) Interfaces & Schemas (For LLM Collaborators)

**Book**
```json
{
  "id": "uuid",
  "title": "str",
  "path": "str",
  "pages": 200,
  "created_at": "ts"
}
```

**Chunk**
```json
{
  "id": "uuid",
  "book_id": "uuid",
  "page_start": 12,
  "page_end": 14,
  "text": "str",
  "md5": "str"
}
```

**Card**
```json
{
  "id": "uuid",
  "book_id": "uuid",
  "type": "basic|cloze",
  "question": "str",
  "answer": "str",
  "source_chunk_id": "uuid",
  "ef": 2.5,
  "interval": 0,
  "repetitions": 0,
  "due_date": "ts"
}
```

**Q&A Response**
```json
{
  "answer": "str",
  "citations": [{"chunk_id":"uuid","page":13,"snippet":"str"}]
}
```

---

## 6) Configuration (Env Vars)

```
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
OTLP_ENDPOINT=http://<grafana-agent>:4317
DATA_DIR=./data
INDEX_DIR=./data/index
DB_PATH=./data/app.db
MAX_CHUNK_TOKENS=1000
CHUNK_OVERLAP=100
TOP_K=5
SIM_THRESHOLD=0.25
```

---

## 7) Makefile Targets (Automation)

```
setup:        # install deps
run:          # start uvicorn with reload
ingest:       # ingest a pdf
build-index:  # build embeddings + faiss
qa:           # ask a question against a book
gen-cards:    # generate N cards for a chapter
export-anki:  # export csv/apkg
fmt:          # format code
test:         # run tests
```

---

## 8) Testing Plan (Minimal but Meaningful)

**Unit**
- `test_chunking.py`: chunk count, overlap rules, empty page handling.
- `test_retrieval.py`: known query returns known chunk (golden test).
- `test_cards.py`: schema validation, dedup, cloze braces.

**Manual Acceptance**
- Script with 20 canonical questions; log accuracy and citation quality.
- 10‑card study session; verify SM‑2 state transitions.
- Anki import of exported deck.

---

## 9) Observability Blueprint

**Traces**
- Spans: `ingest`, `embed.batch`, `index.build`, `retrieve`, `qa.answer`, `cards.generate`, `srs.update`.

**Metrics** (Prometheus via OTLP → Grafana)
- `bc_requests_total{route}`
- `bc_latency_seconds_bucket{route}`
- `bc_embedding_tokens_total`
- `bc_llm_tokens_total{role}`
- `bc_flashcards_generated_total`
- `bc_cost_eur_total` (computed estimate)

**Logs** (to stdout → Grafana Loki if configured)
- Info: major lifecycle events; Warn/Error: failures with correlation IDs.

**Dashboards**
- Request rate, p95 latency, error rate
- Token & cost trends
- Cards/day and average review grade

---

## 10) Risks & Mitigations (POC)

- **Token cost spike** → Batch embeddings, cache results, small embedding model.
- **Poor citations** → Increase chunk overlap, add reranker pass (future), raise SIM_THRESHOLD.
- **Slow TTFB** → Prebuild index; lazy‑load UI; use streaming responses.
- **PDF extraction noise** → Post‑process whitespace, hyphenation fixes, remove headers/footers.

---

## 11) End‑State Documentation Checklist

By the end of the MVP, your repo should include:

1. **README.md** — Quickstart (install, run, ingest, QA, generate cards, review, export). GIF or screenshots.
2. **ARCHITECTURE.md** — Components, data flows, sequence diagrams for ingest → index → RAG → cards → SRS.
3. **OBSERVABILITY.md** — How to point OTLP to your Grafana, dashboard JSON exports.
4. **CONFIG.md** — All env vars with defaults and examples (`.env.example`).
5. **SCHEMAS.md** — JSON schemas for Book/Chunk/Card/Q&A; DB schema.
6. **TESTING.md** — Unit tests, manual acceptance script, accuracy log template.
7. **RUNBOOK.md** — Common ops (rebuild index, rotate keys, clear cache), troubleshooting.
8. **PROMPTS.md** — Canonical prompts for Q&A and flashcard generation; few‑shot examples.
9. **ROADMAP.md** — Post‑MVP ideas (EPUB, notes compare, reranker, hybrid search, better UI).
10. **LICENSE + NOTICE** — Even if internal, include a permissive license header and third‑party notices.

---

## 12) LLM Collaboration Hints (for your AI PM/Copilot)

- “Generate FastAPI endpoints for `/ingest`, `/qa`, `/cards`, `/review` following the schemas in **SCHEMAS.md**.”
- “Write a `cards.generate` function that yields JSON lines streaming and validates with pydantic.”
- “Instrument `qa.answer` with OTEL spans and metrics as per **Observability Blueprint**.”
- “Draft a Makefile with the targets listed and sensible commands.”
- “Create unit tests named in **Testing Plan**, using pytest parametrization.”

---

## 13) Final Acceptance (Demo Script)

1. Start app `make run`; open Grafana dashboard.
2. Upload a known technical PDF (e.g., chapter 1 of a freely available doc).
3. Show ingest progress; index build completes.
4. Ask 3 domain questions; show citations.
5. Generate 20 flashcards; open Review; complete 5 cards with SM‑2.
6. Export CSV; import into Anki; show deck on phone.
7. Point to Grafana panels showing the interactions.

> If every step above works without manual fixes and within the time bounds stated, your MVP is done.

