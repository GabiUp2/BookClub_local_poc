# BookClub — Universal Context Brief

> **Purpose of this file:** Any LLM, any IDE, any agent can read this file to understand the project, current state, and how to work on it. Keep this file updated as the project evolves. It is the single source of truth for onboarding a new context window.

**Last updated:** 2026-03-27

---

## What is BookClub?

An internal-to-standalone tool that turns technical PDFs into flashcards and spaced-repetition decks — powered by LLM + retrieval — to help engineers (and eventually anyone) retain and apply what they read.

**Core principle:** The human does the hard work (reading). BookClub amplifies retention through active recall, not passive consumption.

## Business Model

- **Free (Desktop):** Ships with open-source LLM (Ollama). Runs fully offline. Target: libraries, students, underserved communities.
- **Paid (Cloud):** Phone app, multiple LLM providers, proprietary connectors. Target: professionals keeping up with technology.
- Architecture must support fully offline operation from day one.

## Current State (2026-03-27)

- **Branch:** `bootdev_ai_agent_project` is current (contains AI agent learning exercise + observability infra)
- **What's built:** Full observability stack (Prometheus, Grafana, Loki, Tempo, Alloy), FastAPI server with instrumented endpoints, demo fault injection, 5+ Grafana dashboards, frontend scaffold (Next.js 14)
- **What's stubbed:** `/ingest`, `/generate_flashcards`, `/srs`, `/anki_export` — return `{"status": "not_implemented"}`
- **What's not started:** PDF chunking/embedding, Qdrant integration, flashcard generation, SRS review UI, Anki export

## Why Observability is Mature

Bartosz gave presentations on distributed systems observability at DXC. BookClub was the demo vehicle. Frontend/backend were deliberately separated to show end-to-end trace flow. This is intentional, not over-engineered.

## Related Repos & Learning

- **RAG Search Engine:** `/home/gabiup2/Projects/rag-search-engine` (branch: dev). Boot.dev RAG course. ~40-50% complete. Covers BM25, TF-IDF, embeddings, chunking, cosine similarity. ColBERT and hierarchical structures are research interests, not yet implemented.
- **AI Agent branch:** `bootdev_ai_agent_project` in this repo. Boot.dev AI agent course. Gemini function calling agent.
- **First BookClub RAG implementation** should align with the boot.dev course approach (intentionally naive, then iterate).

## Working Expectations

1. **Learning vehicle first.** Do not optimize only for fastest completion. Prefer solutions that preserve understanding, inspectability, debuggability, and clear architecture.
2. **Explain tradeoffs.** Keep key logic visible. Avoid unnecessary abstraction.
3. **Acceptance test first** → understand behavior → unit tests for edge cases → implementation → documentation.
4. **Makefile** is the operational layer. Consider alternatives only with good justification.
5. **ADHD-aware workflows.** Chunked, dopamine-friendly work sessions. Clear next steps. Visible progress.

## Tech Stack

| Layer | Current | Notes |
|-------|---------|-------|
| Backend | FastAPI (Python 3.11, uv, Gunicorn) | Multiprocess Prometheus metrics |
| Frontend | Next.js 14, TypeScript, Tailwind, CopilotKit | Scaffold only |
| Vector DB | Qdrant (configured, not wired) | May start with simpler approach per boot.dev course |
| LLM | Ollama (local) / OpenAI (remote) | Provider must be abstracted |
| Observability | Prometheus + Loki + Tempo + Alloy + Grafana | Mature, production-like setup |
| Infra | Docker Compose (9 services) | Local-first, no cloud dependencies |
| Tests | pytest (async, xdist), Jest | Integration + unit + observability tests |

## Maintenance Rules for Agents

- **`.context_docs/decisions/`** — When making a significant architecture or technology choice, create an ADR (Architecture Decision Record) in this folder. Use format `ADR-NNN-short-title.md`. All agents working on this project should maintain this practice.
- **`.context_docs/progress/checklist.md`** — Update when completing or adding tasks. This is the shared progress view.
- **`.context_docs/CONTEXT.md`** — Update when project state changes significantly (new phase, major decision, stack change).

## Key Documents

- `docs/pre_work_context/book_club_mvp_plan_local_poc.md` — Original 8-step execution plan
- `docs/pre_work_context/book_club_context_revised.md` — Project context and success metrics
- `ROADMAP.md` — Granular task checklist by area
- `.context_docs/` — This folder. Vision, decisions, progress tracking.

## Planned Future Work

- **Advanced presentation:** Dev-process observability with Pyroscope, commit/branch metrics, LLM token tracking
- **RAG pipeline:** Align with boot.dev course completion, then iterate toward ColBERT/advanced retrieval
- **Vision crystallization:** See `.context_docs/vision/`
