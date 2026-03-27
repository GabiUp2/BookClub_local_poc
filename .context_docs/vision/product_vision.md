# BookClub — Product Vision & PRD (v0.1)

**Date:** 2026-03-27
**Author:** Bartosz Wichowski + Claude (vision crystallization session)
**Status:** Draft — requires validation

---

## Problem Statement

Engineers and technical professionals read books, papers, and documentation constantly — but retention is abysmal. Studies on the forgetting curve (Ebbinghaus) suggest ~70% of learned material is forgotten within 24 hours without active recall. Notes are siloed, passive, and rarely revisited. Existing tools (Anki, SuperMemo) require manual card creation — a tedious barrier that kills adoption.

**Who experiences this:** Engineers, consultants, students, self-learners — anyone who reads technical material for professional development.

**Cost of not solving:** Wasted reading time, repeated lookups, shallow knowledge that doesn't transfer to practice, career stagnation in fast-moving fields.

**Broader impact:** In underserved communities, access to quality education materials exists (libraries, open textbooks) but retention support does not. A child studying math at a library has the book but no tutor to quiz them.

---

## Goals

1. **Time-to-first-value < 3 minutes:** From dropping a PDF to reviewing first flashcards.
2. **Retention improvement ≥ 25%** (self-reported) after 2 weeks of use vs. reading alone.
3. **Zero cloud dependency for core loop:** Ingest → generate cards → review → export works fully offline with a local LLM.
4. **5+ internal users actively reviewing** within first month of MVP release at DXC.
5. **Anki-compatible export** so users aren't locked in — they can take their cards anywhere.

---

## Non-Goals (v1)

| Non-Goal | Rationale |
|----------|-----------|
| EPUB/MOBI support | PDF-only keeps scope tight. Add formats after core loop is validated. |
| Team/collaboration features | Solo learning first. Social features are a different problem. |
| Fancy UI/UX | Minimal, fast, reliable. Don't invest in polish before validating the learning loop. |
| Multilingual support | English-first. Internationalization is a later concern. |
| Mobile app | Desktop-first. Cloud/mobile is the paid tier, comes after desktop validation. |
| Custom LLM fine-tuning | Use off-the-shelf models. Fine-tuning is a research project, not an MVP task. |
| Real-time collaboration or shared decks | Individual learning is the core. Sharing is a future social feature. |

---

## User Personas & Stories

### Persona 1: Working Engineer (Primary — Paid tier target)

> "I read 2-3 technical books a year but retain maybe 20% of what I read. I want to actually remember and apply what I learn."

- As a working engineer, I want to upload a technical PDF and get flashcards generated automatically so that I don't spend hours creating cards manually.
- As a working engineer, I want flashcards to reference specific pages/sections of my book so that I can go back and re-read the source when a card is unclear.
- As a working engineer, I want a spaced repetition schedule so that I review cards at optimal intervals for long-term retention.
- As a working engineer, I want to export my deck to Anki so that I can review on my phone during commutes.
- As a working engineer, I want to ask questions about the book and get answers grounded in the text so that I can clarify concepts without switching to a search engine.

### Persona 2: Student / Self-Learner (Primary — Free tier target)

> "I study at the library and have access to textbooks but no tutor. I need something to test me on what I've read."

- As a student, I want to run BookClub on the library computer without internet so that I can study anywhere.
- As a student, I want BookClub to quiz me on material I've actually read so that I practice active recall, not passive review.
- As a student, I want to see my progress over time so that I stay motivated to keep studying.
- As a student, I want the app to work without creating an account or paying so that there's no barrier to starting.

### Persona 3: Technical Upskiller (Secondary)

> "I'm transitioning into AI/data from a different role. I need to build deep knowledge quickly."

- As a career switcher, I want to generate cards from multiple books/docs on the same topic so that I build a comprehensive knowledge base.
- As a career switcher, I want cloze-deletion cards (fill-in-the-blank) for definitions and formulas so that I memorize precise terminology.

---

## Requirements

### Must-Have (P0) — The core learning loop

**P0-1: PDF Ingestion & Chunking**
- Upload a PDF → parse text → chunk semantically (heading-aware, ~800-1200 tokens, with overlap)
- Persist: book record, chunk records with page references, text, and content hash
- Acceptance criteria:
  - [ ] A 200-page technical PDF is ingested in < 60 seconds
  - [ ] > 95% of chunks have non-empty, meaningful text
  - [ ] Chunks preserve heading/section context
  - [ ] Duplicate uploads are detected (content hash)

**P0-2: Embedding & Vector Index**
- Embed chunks using sentence-transformers (local) or OpenAI embeddings (remote)
- Build searchable vector index
- Acceptance criteria:
  - [ ] Index build completes without error
  - [ ] A sample query returns semantically relevant top-k chunks (manual verification on 10 queries)
  - [ ] Embedding model is abstracted — can swap without changing application code

**P0-3: Flashcard Generation**
- Generate 20-30 flashcards (basic Q&A + cloze deletion) from selected chapters/sections
- Each card references its source chunk (page, section)
- Cards validated against schema, deduplicated
- Acceptance criteria:
  - [ ] ≥ 20 valid cards generated per chapter in < 90 seconds
  - [ ] ≥ 70% of sampled cards are clear, atomic, and unambiguous
  - [ ] All cards have a traceable source_chunk_id
  - [ ] LLM provider is abstracted (works with Ollama and OpenAI)

**P0-4: Spaced Repetition Engine (SM-2)**
- SM-2 scheduling: easiness factor, interval, repetitions, due_date per card
- `/review/next?limit=10` returns due cards; `/review/submit` updates schedule
- Acceptance criteria:
  - [ ] Card due dates update correctly after review
  - [ ] Subsequent calls return updated queue (reviewed cards disappear until due)
  - [ ] A 10-card session completes in < 5 minutes without errors

**P0-5: Minimal Review UI**
- Show one card at a time → reveal answer → grade (0-5) → next
- Display progress (cards remaining, session stats)
- Acceptance criteria:
  - [ ] User can complete a full review session through the UI
  - [ ] Grade submissions update the SRS schedule
  - [ ] Session stats are visible (cards done, average grade)

**P0-6: Anki Export**
- Export deck to CSV (minimum) with: question, answer, tags, source
- Optional: .apkg via genanki
- Acceptance criteria:
  - [ ] Exported CSV imports into Anki without errors
  - [ ] ≥ 95% of cards render correctly in Anki

**P0-7: Fully Offline Operation**
- Core loop (ingest → cards → review → export) works without internet using Ollama
- Acceptance criteria:
  - [ ] With network disabled and Ollama running, the full loop completes successfully
  - [ ] No hard-coded API calls to external services in the core path

### Nice-to-Have (P1) — Significant improvements

**P1-1: Retrieval-Augmented Q&A with Citations**
- Ask questions about the book → get answers grounded in the text with chunk citations
- "I don't know" response when similarity is below threshold
- Acceptance criteria:
  - [ ] ≥ 85% of test questions return correct supporting snippets
  - [ ] Latency p95 < 3 seconds

**P1-2: Observability of Learning Metrics**
- Track: flashcards generated/day, review sessions/day, average grade, retention curve
- Visible in Grafana (leverages existing stack)
- Acceptance criteria:
  - [ ] At least 3 Grafana panels showing learning metrics
  - [ ] Data updates in near-real-time after review sessions

**P1-3: Cost Estimator**
- Track prompt/embedding tokens per session → show estimated cost
- Acceptance criteria:
  - [ ] Token counts visible in metrics
  - [ ] Cost estimate displayed (configurable $/token rate)

### Future Considerations (P2) — Design for but don't build

**P2-1: Cloud Tier & Phone App**
- Sync decks to cloud → access from mobile
- Multiple LLM provider marketplace
- Payment/subscription system

**P2-2: Multi-Book Knowledge Base**
- Cross-reference cards and Q&A across multiple books
- Topic-level clustering and knowledge graph

**P2-3: Tutor Mode**
- Conversational study companion that adapts to knowledge gaps
- Socratic questioning based on weak cards

**P2-4: Dev-Process Observability Presentation Material**
- Commit/branch metrics labels, Pyroscope integration, test execution comparison across branches
- LLM token usage metrics per provider

**P2-5: Advanced Retrieval (ColBERT, Hybrid Search)**
- Late interaction retrieval, BM25 + dense hybrid, reranking
- Aligned with boot.dev course completion

---

## Success Metrics

### Leading Indicators (first 2 weeks)
| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to first flashcards | < 3 min | Instrumented span duration |
| Flashcard quality (manual sample) | ≥ 70% clear & atomic | 20-card sample per book |
| Answer grounding accuracy | ≥ 85% correct citations | 20-query spot check |
| Session completion rate | ≥ 80% | Started vs. completed review sessions |

### Lagging Indicators (first 2 months)
| Metric | Target | Measurement |
|--------|--------|-------------|
| Active reviewers (internal) | ≥ 5 users | Unique users with ≥ 2 sessions in 10 days |
| Avg. cards reviewed/week | ≥ 15 per user | SRS review logs |
| Self-reported retention boost | ≥ 25% | Quick survey after 2 weeks |
| Stability | 0 crashes in 30-min session | Error rate monitoring |

---

## Open Questions

| # | Question | Owner | Blocking? |
|---|----------|-------|-----------|
| 1 | Which embedding model gives best quality/speed for technical text on consumer hardware? (MiniLM vs instructor-xl vs nomic-embed) | Engineering | Yes — affects P0-2 |
| 2 | SM-2 vs FSRS? SM-2 is open (attribution req). SM-18 is proprietary/trade secret. FSRS is MIT, academic-backed, in Anki 23.10+. FSRS has Python/Rust/JS implementations. Worth an ADR. | Engineering | No — SM-2 is fine for v1, but FSRS alignment with Anki is compelling |
| 3 | Should chunking be heading-aware (requires PDF structure parsing) or fixed-size-with-overlap (simpler)? | Engineering | No — start with simpler, iterate |
| 4 | What's the minimum viable LLM for offline flashcard generation? (Llama 3.2 3B? Phi-3?) | Engineering | Yes — affects offline viability |
| 5 | How to handle PDFs with heavy diagrams/tables/code? Text extraction will miss these. | Engineering | No — acknowledge limitation in v1, note for v2 |
| 6 | Licensing model for free tier — MIT? Apache 2.0? AGPL? | Bartosz | No — but decide before public release |

---

## Phasing

### Phase 0 — Current (Complete)
Observability infrastructure, FastAPI skeleton, frontend scaffold, demo harness.

### Phase 1 — Core Learning Loop (Next)
P0-1 through P0-7. Aligned with boot.dev RAG course completion. Start with naive RAG, instrument everything, measure quality.

**Approach:** Implement in order (ingest → embed → cards → SRS → UI → export). Each step gets acceptance tests first, then implementation, then observability verification.

### Phase 2 — Refinement
P1-1 through P1-3. Q&A with citations, learning metrics dashboards, cost tracking.

### Phase 3 — Public Release Prep
Offline validation, packaging (Desktop app via Tauri or Electron?), documentation, license decision.

### Phase 4 — Cloud Tier
P2-1. Requires a separate architecture discussion.

---

## Competitive Landscape (Brief)

| Tool | Strength | BookClub Differentiator |
|------|----------|------------------------|
| **Anki** | Gold standard SRS, massive community, now ships FSRS | Manual card creation is the adoption killer. BookClub automates this. **Anki is an ally, not a competitor** — we export to Anki format. Users keep their Anki workflow, BookClub fills the card-creation gap. |
| **SuperMemo** | Advanced SRS algorithm (SM-18, proprietary) | Closed ecosystem, expensive, steep learning curve. SM-2 is open (© SuperMemo World, 1991). SM-18 is trade secret / not licensed. FSRS (open-source, MIT) is a modern alternative backed by academic research. |
| **RemNote** | Notes + flashcards integrated | Requires you to take notes in their format. BookClub works with any PDF. |
| **Readwise** | Highlight-based review | Highlights ≠ flashcards. No active recall, no question generation. |
| **NotebookLM (Google)** | AI-powered Q&A on documents | No SRS, no flashcard export, cloud-only, no offline. |
| **Quizlet** | Simple flashcard creation | Manual creation, no PDF ingestion, no SRS (just basic repetition). |

**BookClub's unique position:** The only tool that (a) auto-generates cards from what you actually read, (b) uses proper SRS for retention, (c) works fully offline, (d) doesn't lock you in (Anki export), and (e) complements rather than replaces existing SRS tools.

**SRS Algorithm Note:** SM-2 is open with attribution requirement. SM-18 is proprietary/trade secret — SuperMemo no longer licenses it. FSRS (Free Spaced Repetition Scheduler) is MIT-licensed, backed by academic research (DSR model), implemented in multiple languages (Python, Rust, Go, JS), and already integrated into Anki 23.10+. **Decision needed: SM-2 (simpler, well-understood) vs FSRS (modern, better performance) — see ADR backlog.**

---

## Alignment with Learning Goals

This is a learning vehicle. Each phase teaches something:

- **Phase 1:** RAG fundamentals (chunking, embeddings, retrieval, prompt engineering), aligns directly with boot.dev course
- **Phase 2:** Observability of ML/LLM systems (token tracking, quality metrics, cost estimation)
- **Phase 3:** Packaging, distribution, offline-first architecture decisions
- **Phase 4:** Cloud architecture, multi-tenancy, payment systems

The constraint is intentional: metrics-grounded learning. Every implementation decision should be observable — you should be able to see in Grafana whether a change improved or degraded the system.
