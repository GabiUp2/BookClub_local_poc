# 📚 The Book Club — Project Context (Revised for MVP Execution)

**Version:** 0.3 (Revised)  
**Date:** 2025-10-04  
**Author:** Bartosz Wichowski (DXC Technology), with strategic review

---

## 🧠 One-liner

> An internal tool that turns technical PDFs into flashcards and spaced-repetition decks — powered by LLM + retrieval — to help engineers retain and apply what they read.

---

## 🧩 Problem Statement & Opportunity (Updated)

- **Problem:** Engineers read technical books/docs but struggle with retention and consistent application. Notes are siloed, Q&A is limited, and recall is poor.
- **Opportunity:** Deliver *tangible value in minutes* by turning passive reading into active retention using flashcards and spaced repetition.
- **Why now:** Internal LLM infra is becoming accessible; company-wide AI enablement initiatives (Guilds & Chapters) are ramping up.

**Primary users:** Engineers and consultants in AI, Data, Software, DevOps.  
**Secondary users:** Interns, new hires, technical upskillers.

---

## 🎯 Revised MVP Scope

### ✅ Core MVP
1. **PDF Upload + Parsing** (initially PDF only)
2. **Semantic Chunking + Embeddings**
3. **LLM-Powered Flashcard Generation** (Q&A + Cloze)
4. **Spaced Repetition Engine (SM-2)**
5. **Review UI (minimal, 5–10 cards/session)**
6. **Anki-compatible Export**
7. **Local Storage (for POC)**
8. **Entra ID SSO (for internal MVP)**
9. **Grafana-based Observability (via local setup)**

### 🚫 Deferred Features
- EPUB/MOBI ingestion
- Notes import and comparison
- Essay prompt generation
- Shared reading plans and team workspaces
- Multilingual support
- Notion integration
- Evals framework, dashboards (post-MVP)

---

## 📊 Success Metrics (MVP Phase)

| Metric | Target |
|--------|--------|
| Users uploading and generating flashcards | ≥ 5 users |
| Time-to-first-output (upload → flashcards) | < 3 min |
| Review sessions per user | ≥ 2 within 10 days |
| Avg. flashcards reviewed/week | ≥ 15 |
| Retention boost (self-reported) | ≥ 25% |

---

## 🧱 Architecture (MVP Phase)

| Layer | Tooling |
|-------|---------|
| Frontend | React/Next.js (minimal UI) |
| Backend | FastAPI or Node (user's discretion) |
| Auth | Entra ID SSO |
| Storage | Local storage (user POC), Azure Blob (future) |
| Vector DB | Qdrant (local or cloud) |
| Embeddings | Instructor-xl, MiniLM or OpenAI embeddings |
| LLM | OpenAI GPT-4 or Llama 3 (via Ollama, LM Studio) |
| Observability | Prometheus + Grafana + Loki (local setup) |
| Export | Anki-compatible CSV or .apkg |

---

## 📆 MVP Execution Plan (6 Stages)

See accompanying document: **Book Club MVP — Executable Plan (Solo POC)**.

Stages:
1. Bootstrap project environment + storage
2. Ingest PDF and generate embeddings
3. Generate flashcards via LLM
4. Implement review + SRS engine
5. (Optional) Add Q&A with citation
6. Document, package and demo

---

## 🧾 Change Log

- **2025-10-04:** Strategic reduction and refocus of MVP scope based on feasibility, user-first value delivery, and faster validation.
- Removed features not required to deliver value in first 5 minutes (essay prompts, notes ingestion, dashboards, cohorts).
- Reframed success metrics to focus on flashcard output and usage instead of vanity stats.
- Defined clear 6-stage execution path, tracked with Grafana logs.
- Shifted from team cohort model to individual proof-of-value with minimal dependencies.

---

## ✍️ Final Notes

This revised context focuses on building a **Minimum Lovable Learning Tool** — fast, focused, and valuable from day one. Post-validation, additional features can be modularly integrated.

Next Step: Build POC locally. Validate with 1–3 engineers. Expand only from proven behavior.

---

