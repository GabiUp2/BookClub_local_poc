# Capabilities Plan — What We Can Do and What It Enables

**Date:** 2026-03-27
**Scope:** What tools, plugins, and workflows are available or installable, what effect each has, and recommended priorities.

---

## 1. What We Already Have

### Installed Plugins (Claude Desktop / Cowork)

| Plugin | Key Skills | Value for BookClub |
|--------|-----------|-------------------|
| **Productivity** | `task-management`, `memory-management`, `start`, `update` | Track tasks in TASKS.md, persist context across sessions, decode shorthand. Good for ADHD workflow — visible, persistent task state. |
| **Engineering** | `architecture`, `system-design`, `code-review`, `testing-strategy`, `debug`, `documentation`, `tech-debt`, `standup`, `deploy-checklist`, `incident-response` | ADR creation for key decisions, test strategy design, structured debugging, technical documentation generation. Core utility for the entire project. |
| **Design** | `design-critique`, `accessibility-review`, `ux-copy`, `user-research`, `research-synthesis`, `design-system`, `design-handoff` | UI/UX review when building the review interface, accessibility audit (critical for library/equity use case), user research synthesis when validating with colleagues. |
| **Data** | `analyze`, `create-viz`, `build-dashboard`, `explore-data`, `statistical-analysis`, `sql-queries`, `validate-data`, `data-context-extractor` | Analyze test metrics, build HTML dashboards for progress visualization, statistical analysis of flashcard quality/retention metrics, data exploration of usage patterns. |
| **Product Management** | `write-spec`, `roadmap-update`, `competitive-brief`, `sprint-planning`, `metrics-review`, `stakeholder-update`, `synthesize-research` | Vision crystallization (write-spec), roadmap management, competitive analysis against Anki/SuperMemo/RemNote, sprint planning for ADHD-friendly work chunks. |

### Connected MCPs

| MCP | Tools | Value |
|-----|-------|-------|
| **Context7** | `resolve-library-id`, `query-docs` | Pull up-to-date docs for any library (FastAPI, OTEL, Qdrant, sentence-transformers) directly in conversation. Saves context-switching. |
| **Microsoft Learn** | `microsoft_docs_search`, `microsoft_docs_fetch`, `microsoft_code_sample_search` | Relevant for Entra ID SSO (future), Azure Blob storage (cloud tier), Microsoft Fabric knowledge. |
| **Microsoft 365** | Outlook email/calendar, Teams chat, SharePoint | Search for related DXC communications, find presentation materials, schedule focused work blocks. |
| **Chrome Automation** | Full browser control | Navigate Grafana dashboards, capture screenshots for docs/presentations, interact with boot.dev course pages. |
| **Scheduled Tasks** | `create_scheduled_task`, `list`, `update` | Automate recurring checks (e.g., weekly progress summaries, test health reports). |

### Core Tools

| Tool | Value |
|------|-------|
| Bash, Read, Write, Edit, Glob, Grep | Full filesystem access, code editing, search. The foundation. |
| WebSearch, WebFetch | Research libraries, check docs, verify approaches. |
| TodoWrite | In-session task tracking with visible progress. |

---

## 2. What We Could Add

### High-Value Additions

#### A. GitHub MCP Connector
**What it does:** Direct access to GitHub issues, PRs, commits, actions from within Claude.
**Effect:** Create issues from conversation, review PRs, check CI status, read commit history — without leaving the editor.
**Enables:** Tighter loop between planning and execution. When we discuss a feature, I can immediately create an issue. When CI fails, I can read the logs directly.
**Priority:** HIGH — this project lives on GitHub.

#### B. Custom BookClub Plugin (MCP + Skills)
**What it does:** A Cowork plugin bundling BookClub-specific skills and an MCP server that agents can communicate with.
**Effect:** Any Claude session instantly knows how to operate BookClub's infrastructure. Think broader: MCP endpoints that expose BookClub's own data (card quality metrics, review stats, ingestion status) so agents can reason about the project state.
**Enables:** "Check if the observability stack is healthy" or "What's the flashcard quality score for the last ingestion?" as natural agent actions. Also enables other tools/agents to interact with BookClub programmatically.
**Priority:** MEDIUM — worth doing once the core loop exists. Design the MCP interface early though.

#### C. Taskwarrior / taskd MCP (Custom)
**What it does:** MCP connector to taskwarrior + self-hosted taskd server.
**Effect:** Tasks managed in taskwarrior are visible to Claude across all IDEs/sessions. Task state lives in a real task management system, not ephemeral markdown.
**Enables:** True multi-machine, multi-tool task continuity through a system Bartosz already knows and controls. Could also feed task metadata into Grafana for the dev-process observability presentation.
**Priority:** MEDIUM — write this as a standalone MCP. Good learning exercise for MCP development.

#### D. BookClub Agent(s)
**What it does:** Specialized agents that can be invoked to perform BookClub-specific workflows.
**Effect:** Composable automation — e.g., an agent that runs the full "ingest PDF → verify in Grafana → report quality" pipeline.
**Enables:** Delegation of repetitive workflows to agents, demonstration material for presentations.
**Priority:** LOW for now — design the interfaces, build agents when there's something to automate.

---

## 3. Workflows This Enables

### A. Planning Workflow (this session)
```
Product Management (write-spec, roadmap-update)
  + Engineering (architecture, system-design)
  + Data (analyze, statistical-analysis)
  → Vision doc, validated roadmap, ADRs for key decisions
```

### B. Implementation Workflow (per feature)
```
1. Engineering (testing-strategy) → acceptance test design
2. Write acceptance test (you or lighter model)
3. Engineering (system-design) → implementation approach
4. Implement (you or lighter model, guided by plan)
5. Engineering (code-review) → review before merge
6. Engineering (documentation) → update docs
7. Data (validate-data) → verify metrics/quality
```

### C. Presentation Workflow (future)
```
1. Data (build-dashboard) → HTML dashboard of dev metrics
2. Data (create-viz) → publication-quality charts
3. Design (design-critique) → review presentation visuals
4. Engineering (documentation) → write the narrative
```

### D. ADHD-Friendly Review Workflow
```
1. Productivity (task-management) → see what's pending
2. Product Management (sprint-planning) → pick a small, completable chunk
3. Engineering (standup) → generate status from git activity
4. Productivity (update) → sync progress
```

---

## 4. Context Storage Approach

### Problem
Multiple IDEs (VSCode, Cursor, Windsurf, Neovim), multiple agents (Claude Desktop, CLI, Copilot, Codex), different machines. No single proprietary context store works across all of them.

### Solution: Repo-native context in `.context_docs/`

**Why the repo:**
- Git-tracked → versioned, diffable, branchable
- Plain markdown → readable by any LLM, any editor, any human
- Available on every machine that has the repo cloned
- Can be referenced in CLAUDE.md, .cursorrules, .windsurfrules, copilot instructions, etc.

**Structure:**
```
.context_docs/
├── CONTEXT.md              ← Universal briefing (any LLM reads this first)
├── capabilities_plan.md    ← This file
├── vision/
│   ├── product_vision.md   ← What BookClub is and why
│   ├── roadmap.md          ← Prioritized roadmap (replaces/extends ROADMAP.md)
│   └── competitive.md      ← Competitive landscape
├── decisions/
│   └── ADR-001-*.md        ← Architecture Decision Records
└── progress/
    └── checklist.md        ← Current sprint/phase checklist
```

**Cross-IDE integration:**
- `CLAUDE.md` → add: "Read .context_docs/CONTEXT.md for full project context"
- `.cursorrules` → add equivalent instruction
- `.windsurfrules` → add equivalent instruction
- Neovim/CLI → reference in project-local config

**Makefile as operational glue** stays — it's universal, shell-native, and every tool can call `make`. No reason to change it for this project.

---

## 5. Recommended Next Steps (in order)

1. **Now:** Crystallize the product vision (using `write-spec` + `competitive-brief` skills)
2. **Now:** Write a revised roadmap that aligns with boot.dev course completion + vision
3. **Soon:** Set up cross-IDE context files (CLAUDE.md update, .cursorrules, etc.)
4. **Soon:** Create first ADR (offline-first architecture)
5. **When ready:** Install GitHub MCP connector
6. **Later:** Create custom BookClub plugin once workflows are stable
