# BookClub — Progress Checklist

**Updated:** 2026-03-27
**Current Phase:** Phase 0 → Phase 1 transition

---

## Phase 0 — Infrastructure & Observability ✅

- [x] Docker Compose stack (9 services)
- [x] FastAPI backend with health/metrics endpoints
- [x] Prometheus metrics (multiprocess Gunicorn)
- [x] Loki log aggregation via Alloy
- [x] Tempo distributed tracing via Alloy
- [x] Grafana dashboards (5 pre-built)
- [x] OTEL instrumentation (backend traces, metrics, logs)
- [x] OTEL instrumentation (frontend browser traces)
- [x] W3C traceparent propagation (frontend → backend)
- [x] Metrics ↔ logs ↔ traces correlation in Grafana
- [x] Demo fault injection middleware
- [x] `@track_timing` execution timing decorator
- [x] Next.js 14 frontend scaffold
- [x] PDF upload endpoint (with validation + tracing)
- [x] Makefile operational layer (70+ targets)
- [x] Presentations on distributed systems observability

## Phase 0.5 — Learning Alignment & Foundation (In Progress)

### Boot.dev RAG Course (rag-search-engine repo, branch: dev)

Full curriculum: 12 chapters. Uses Gemini API for LLM steps.

- [x] Ch 1: Preprocessing — normalize and clean raw corpora
- [x] Ch 2: TF-IDF — inverted indexes and weighting schemes
- [x] Ch 3: Keyword Search — BM25 refinements and metadata boosts
- [x] Ch 4: Semantic Search — embeddings, similarity metrics, vector DBs
- [x] Ch 5: Chunking — context-preserving segmentation (partially done — `search_chunked()` needs finishing)
- [ ] Ch 6: Hybrid Search — blend lexical + semantic scores into unified pipelines
- [ ] Ch 7: LLMs — query expansion, intent correction, retrieval orchestration
- [ ] Ch 8: Reranking — re-score retrieved candidates with rerankers
- [ ] Ch 9: Evaluation — precision, recall, relevance measurement for RAG
- [ ] Ch 10: Augmented Generation — combine retrieved context + LLM → grounded answers
- [ ] Ch 11: Agentic — autonomous agents for iterative query refinement
- [ ] Ch 12: Multimodal — images and cross-modal retrieval

### Boot.dev AI Agent Course (bootdev_ai_agent_project branch)
- [x] Function calling agent with Gemini API
- [ ] Remaining course modules (TBD)

### BookClub Foundation (ADR-001, ADR-002)
- [ ] Create new feature branch for Phase 1 work (off main/master)
- [ ] Set up domain models — `src/book_club/domain/models.py` (Pydantic: Book, Chunk, Card, ReviewResult, SearchResult)
- [ ] Define storage interfaces — `src/book_club/domain/ports.py` (Protocols: BookRepository, ChunkRepository, VectorStore, CardRepository, ReviewRepository)
- [ ] Replace Qdrant with PostgreSQL+pgvector in `docker-compose.yml`
- [ ] Add PostgreSQL Prometheus exporter to observability stack
- [ ] Set up alembic for schema migrations
- [ ] Create initial migration (books, chunks, cards, reviews tables)
- [ ] Implement InMemoryVectorStore (numpy — port boot.dev cosine similarity code)
- [ ] Implement PostgresBookRepository
- [ ] Implement PostgresChunkRepository
- [ ] Implement dependency wiring (`dependencies.py`)
- [ ] Write integration test: repositories satisfy Protocol interfaces
- [ ] Verify PostgreSQL metrics in Grafana

### Weaving Strategy: boot.dev ↔ BookClub

Each boot.dev chapter produces a concept that maps to a BookClub feature.
Rhythm: **learn in course → port to BookClub behind interface → instrument with OTEL → verify in Grafana.**

```
FOUNDATION (do first, enables everything else):
  BookClub: domain models + ports + PostgreSQL repos + InMemoryVectorStore
  BookClub: replace Qdrant with PostgreSQL+pgvector in docker-compose

WEAVE 1 — Retrieval Core:
  boot.dev Ch 5 (finish): search_chunked()    → BookClub P0-1 + P0-2: chunking + InMemoryVectorStore
  boot.dev Ch 6: hybrid search                → BookClub: BM25+semantic fusion in retrieval layer
  boot.dev Ch 8: reranking                    → BookClub: improve chunk selection for card generation

WEAVE 2 — LLM Integration:
  boot.dev Ch 7: LLMs (query expansion)       → BookClub: LLM provider abstraction (Ollama/OpenAI)
  boot.dev Ch 10: augmented generation         → BookClub P0-3: flashcard generation (THE key feature)

WEAVE 3 — Quality & Measurement:
  boot.dev Ch 9: evaluation (precision/recall) → BookClub: RAG quality metrics in Grafana
                                                  + dev-process observability presentation material

WEAVE 4 — Advanced (after MVP):
  boot.dev Ch 11: agentic                     → BookClub P2-3: tutor mode (future)
  boot.dev Ch 12: multimodal                  → BookClub: PDF diagrams/tables handling (future)

PARALLEL (anytime):
  BookClub P0-4: SM-2 SRS engine (independent of RAG pipeline)
  BookClub P0-5: minimal review UI (independent of RAG pipeline)
  BookClub P0-6: Anki export (independent of RAG pipeline)
```

## Phase 1 — Core Learning Loop

### P0-1: PDF Ingestion & Chunking
- [ ] Write acceptance test: ingest 200-page PDF in <60s, >95% non-empty chunks
- [ ] Implement PDF parsing (PyMuPDF)
- [ ] Implement chunking (start with fixed-size-with-overlap per boot.dev, heading-aware later)
- [ ] Persist via BookRepository + ChunkRepository (PostgreSQL)
- [ ] Add OTEL spans for ingest pipeline
- [ ] Verify in Grafana: ingest duration, chunk count, error rate

### P0-2: Embedding & Vector Index
- [ ] Write acceptance test: sample queries return relevant chunks
- [ ] Implement EmbeddingProvider protocol + sentence-transformers adapter
- [ ] Implement InMemoryVectorStore.search() (cosine similarity, boot.dev approach)
- [ ] Add metrics: embedding_tokens_total, embedding_seconds
- [ ] Verify in Grafana: embedding latency, index build time
- [ ] Later: migrate to PgVectorStore (Phase 2 of ADR-001)

### P0-3: Flashcard Generation
- [ ] Write acceptance test: ≥20 valid cards per chapter, ≥70% quality
- [ ] Implement card generation prompt (basic Q&A + cloze)
- [ ] Implement pydantic schema validation + dedup
- [ ] Store cards in DB with source_chunk_id
- [ ] Add metrics: cards_generated_total, generation_seconds, llm_tokens_total
- [ ] Verify in Grafana: generation latency, token cost, card quality proxy

### P0-4: Spaced Repetition Engine (SM-2)
- [ ] Write acceptance test: due dates update correctly, queue reflects schedule
- [ ] Implement SM-2 fields per card (EF, interval, repetitions, due_date)
- [ ] Implement `/review/next` and `/review/submit` endpoints
- [ ] Add metrics: reviews_total, average_grade, cards_due

### P0-5: Minimal Review UI
- [ ] Write acceptance test: complete 10-card session via UI
- [ ] Build card display component (show question → reveal answer → grade)
- [ ] Build session progress display
- [ ] Wire to SRS endpoints

### P0-6: Anki Export
- [ ] Write acceptance test: CSV imports into Anki, ≥95% render correctly
- [ ] Implement CSV export (question, answer, tags, source)
- [ ] Optional: .apkg via genanki

### P0-7: Offline Verification
- [ ] Write acceptance test: full loop with network disabled + Ollama
- [ ] Verify no hard-coded external API calls in core path
- [ ] Document minimum hardware requirements

## Phase 2 — Refinement (Later)

- [ ] Retrieval-Augmented Q&A with citations
- [ ] Learning metrics Grafana dashboards
- [ ] Cost estimator (token tracking)
- [ ] Commit/branch metrics labels
- [ ] Pyroscope integration

## Phase 3 — Public Release Prep (Future)

- [ ] Desktop packaging (Tauri? Electron? evaluate)
- [ ] Offline-first validation
- [ ] License decision
- [ ] Public documentation
- [ ] Landing page

## Phase 4 — Cloud Tier (Future)

- [ ] Cloud architecture design
- [ ] Phone app
- [ ] Multi-LLM provider marketplace
- [ ] Payment/subscription system
