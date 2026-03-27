# ADR-001: Vector Storage — Qdrant vs PostgreSQL + pgvector

**Status:** Accepted
**Date:** 2026-03-27
**Deciders:** Bartosz Wichowski

## Context

BookClub needs a vector store for the semantic search pipeline (P0-2 in the roadmap). The current `docker-compose.yml` includes Qdrant (ports 6333/6334, REST + gRPC), but it has never been wired into application code — the integration is still a stub.

At the same time, the MVP plan calls for relational storage (originally SQLite) for books, chunks, flashcards, and SRS review state. This means the project will need *both* a vector index and a relational database.

**Forces at play:**

1. **Service count.** Docker Compose already has 9 services (Qdrant, app, server, Prometheus, Pushgateway, Loki, Tempo, Alloy, Grafana). Adding PostgreSQL *alongside* Qdrant makes it 10. Replacing Qdrant with PostgreSQL+pgvector keeps it at 9 and unifies two roles into one.

2. **Offline/desktop packaging.** The free tier vision requires minimal dependencies. One database process is simpler to package and support than two (SQLite + Qdrant, or PostgreSQL + Qdrant).

3. **Learning value.** This project is a learning vehicle. Both options teach something different — Qdrant teaches purpose-built vector DB ergonomics; PostgreSQL+pgvector teaches how to extend a general-purpose DB for vector workloads.

4. **Scale.** BookClub's dataset is small. A single book produces hundreds to low thousands of chunks. Even a power user with 50 books would have ~50K vectors. This is far below the scale where dedicated vector DBs show clear advantages.

5. **Boot.dev course alignment.** The RAG course uses simpler approaches (numpy cosine similarity, in-memory). The first implementation should be naive. The vector store is a later upgrade.

## Options Considered

### Option A: Keep Qdrant (dedicated vector DB)

| Dimension | Assessment |
|-----------|------------|
| Complexity | **Medium** — separate service, separate client library, separate API |
| Cost | Free (open source), but extra ~200MB RAM for the container |
| Scalability | Excellent — built for vector workloads, HNSW with SIMD, gRPC API |
| Team familiarity | **Low** — Bartosz hasn't used it yet, no code written against it |
| Offline packaging | **Harder** — requires running a separate process alongside the app |
| Learning value | High for vector DB concepts, lower for general infrastructure |

**Pros:**
- Purpose-built for vector search — rich filtering, payload storage, quantization
- Best-in-class recall at small scale (0.911 vs 0.900 in head-to-head benchmarks)
- gRPC and REST APIs, good Python client (`qdrant-client`)
- If BookClub scales to millions of vectors, Qdrant won't need to be replaced
- Supports on-disk mode for memory-constrained environments

**Cons:**
- Another service to run, monitor, and debug
- Another API to learn and maintain
- Still need a separate relational store for books/cards/SRS state (SQLite or PostgreSQL)
- Two data stores = two backup strategies, two migration strategies, two failure modes
- For <50K vectors, its advanced features (quantization, sharding) aren't needed

### Option B: PostgreSQL + pgvector (unified storage)

| Dimension | Assessment |
|-----------|------------|
| Complexity | **Low** — one service, one client library (asyncpg or SQLAlchemy), one backup |
| Cost | Free (open source), similar RAM footprint to Qdrant for small datasets |
| Scalability | Good — pgvector HNSW handles millions of vectors; pgvectorscale extends further |
| Team familiarity | **Medium** — PostgreSQL is widely known; pgvector is a standard extension |
| Offline packaging | **Easier** — one database process for everything |
| Learning value | High — PostgreSQL is a career-long skill; pgvector teaches extension architecture |

**Pros:**
- **One service for everything:** vectors, books, chunks, cards, SRS state, metadata — all in PostgreSQL
- Removes the need for SQLite entirely — proper ACID transactions, concurrent access, migrations
- pgvector supports HNSW indexes with cosine, L2, and inner product distance
- At BookClub's scale (<50K vectors), pgvector performance is more than sufficient (~sub-ms with HNSW index)
- PostgreSQL is observable — query plans (`EXPLAIN ANALYZE`), `pg_stat_statements`, Prometheus exporter
- Standard tooling: `pg_dump` for backups, `alembic` for migrations, `psql` for debugging
- Aligns with the offline/desktop vision: one `postgres` process vs. `postgres` + `qdrant`
- Rich ecosystem: full-text search (tsvector), JSON storage, CTEs — useful for future features
- pgvector is well-maintained, v0.8+ supports HNSW, active development

**Cons:**
- Not purpose-built for vector search — less sophisticated filtering, no built-in quantization
- HNSW index build is slower than Qdrant for large datasets (irrelevant at our scale)
- If we ever need multi-modal embeddings or complex vector payloads, might outgrow it
- Slightly more setup than SQLite for the simplest case (need to run a postgres service)

### Option C: Start with in-memory/numpy (boot.dev course approach), migrate later

| Dimension | Assessment |
|-----------|------------|
| Complexity | **Lowest** — no external dependencies for vector search |
| Cost | Zero infrastructure cost |
| Scalability | **Poor** — won't survive process restart without serialization, linear scan O(n) |
| Team familiarity | **High** — this is what the boot.dev course teaches |
| Offline packaging | **Easiest** — pure Python |
| Learning value | **Highest for fundamentals** — understand cosine similarity, distance metrics, before abstracting |

**Pros:**
- Aligns perfectly with boot.dev course progression
- Forces understanding of the math before hiding it behind a database
- Zero infrastructure overhead
- Can serialize to disk (numpy `.npy` files) for persistence

**Cons:**
- Doesn't scale past a few thousand vectors efficiently
- No concurrent access (single process)
- Have to build your own persistence, your own index, your own query interface
- Will definitely need replacement for anything beyond a single-book prototype

## Trade-off Analysis

The key tension is between **learning fundamentals** (Option C), **operational simplicity** (Option B), and **specialization** (Option A).

**For BookClub's actual needs** (<50K vectors, needs relational storage anyway, offline-first, solo developer), Option B (PostgreSQL + pgvector) is the sweet spot. It eliminates an entire service, unifies storage, and performs well at our scale.

**However**, the learning vehicle constraint suggests a phased approach:

1. **Start with Option C** (numpy/in-memory) — aligned with boot.dev course, learn the fundamentals
2. **Migrate to Option B** (PostgreSQL + pgvector) — when persistence and concurrent access matter
3. **Keep Option A as a documented alternative** — if BookClub ever needs vector-specific features at scale

This phased approach teaches more than jumping straight to pgvector would:
- Phase 1: "What does vector search actually compute?" (cosine similarity by hand)
- Phase 2: "How does a database index make this fast?" (HNSW in pgvector, `EXPLAIN ANALYZE`)
- Phase 3 (if needed): "When do you need a dedicated vector DB?" (Qdrant's filtering, quantization, sharding)

## Decision

**Replace Qdrant with PostgreSQL + pgvector**, but phase the transition:

1. **Now:** Remove Qdrant from `docker-compose.yml` (it's unused). Add PostgreSQL with pgvector extension.
2. **Phase 1 implementation:** Use numpy/in-memory vectors (boot.dev course approach) with PostgreSQL for relational data only.
3. **Phase 1→2 migration:** Move vectors into PostgreSQL via pgvector when the in-memory approach becomes a bottleneck or when persistence matters.

PostgreSQL handles: books, chunks (with text + metadata), embeddings (via pgvector), flashcards, SRS review state, and future learning metrics.

## Consequences

**What becomes easier:**
- One backup strategy (`pg_dump`), one migration tool (`alembic`), one monitoring target
- Desktop packaging: one database process
- Joins between vectors and relational data (e.g., "find similar chunks *for this book only*")
- Observability: PostgreSQL Prometheus exporter feeds into existing Grafana stack
- The "transactions across vectors and cards" problem disappears (it's all one DB)

**What becomes harder:**
- If we ever need Qdrant-specific features (quantization, multi-vector search, complex payload filtering), we'd need to add it back
- pgvector HNSW index tuning (m, ef_construction, ef_search) is less documented than Qdrant's API
- We lose Qdrant's built-in dashboard UI for inspecting vectors

**What we'll need to revisit:**
- If BookClub cloud tier needs multi-tenant vector isolation, evaluate whether pgvector's row-level security is sufficient vs. Qdrant's collection-per-tenant model
- If advanced retrieval patterns (ColBERT late interaction, multi-vector) require features pgvector doesn't support
- Monitor pgvector project releases — the extension is improving rapidly (v0.8+ HNSW, parallel index builds)

## Action Items

1. [ ] Remove Qdrant service from `docker-compose.yml`
2. [ ] Add PostgreSQL service with pgvector extension to `docker-compose.yml`
3. [ ] Create initial schema migration (alembic) for books, chunks, cards, reviews tables
4. [ ] Add PostgreSQL Prometheus exporter to observability stack
5. [ ] Update `.context_docs/CONTEXT.md` tech stack table
6. [ ] Implement Phase 1 (boot.dev approach) with PostgreSQL for relational data only
7. [ ] When ready for Phase 2: add vector column to chunks table, create HNSW index, benchmark

## References

- [pgvector GitHub](https://github.com/pgvector/pgvector) — open-source, supports HNSW, IVFFlat, cosine/L2/inner product
- [pgvector vs Qdrant benchmarks (Nirant Kasliwal)](https://nirantk.com/writing/pgvector-vs-qdrant/) — at small scale, performance is nearly identical
- [PostgreSQL vs Qdrant 50M benchmark (Tiger Data)](https://dev.to/tigerdata/postgresql-vs-qdrant-for-vector-search-50m-embedding-benchmark-3hhe) — pgvectorscale achieves 471 QPS vs 41 QPS at 50M vectors
- [Qdrant vs pgvector: same speed (Medium)](https://medium.com/@TheWake/qdrant-vs-pgvector-theyre-the-same-speed-5ac6b7361d9d) — at typical RAG scale, the bottleneck is the LLM, not the vector DB
- [HNSW indexes with pgvector (Crunchy Data)](https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector) — tuning guide for m, ef_construction, ef_search
