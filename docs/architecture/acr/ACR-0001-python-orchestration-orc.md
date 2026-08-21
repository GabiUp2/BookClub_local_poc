# ACR-0001 — Replace growing Make orchestration with Python ORC

- **Status:** Accepted
- **Date:** 2026-08-21
- **Owner:** Book Club POC

## Context

The project started with a Makefile as a convenient entry point for a small number of development commands. It now orchestrates environment setup, tests and test metrics, Docker Compose installation, observability verification, browser launching, maintenance, and multi-step integration checks.

The recipes have become increasingly stateful and procedural. They contain shell conditionals, loops, HTTP checks, parsing, waits, platform-specific PowerShell, destructive-operation confirmation, and repeated presentation logic. This makes the Makefile harder to read, test, reuse, and extend safely.

There is also a pragmatic author constraint: Make and non-trivial Make recipes are not a strong skill area for the primary author. Continuing to move increasingly complex orchestration into Make therefore increases maintenance cost and the probability of subtle quoting, shell, dependency, and portability mistakes.

The project needs more orchestration, not less. The current direction would turn the Makefile into an application written accidentally in shell syntax.

## Decision

Introduce an installable Python CLI named **ORC**, invoked as `orc`, implemented with **Typer + Rich** and registered through `[project.scripts]` in `pyproject.toml`.

ORC is an orchestration and presentation adapter only.

It may:

- parse CLI arguments and global flags;
- render colour, tables, progress bars, spinners, warnings, and summaries;
- execute ordered calls;
- perform pre-flight and expected-output checks;
- trigger external tools and local services;
- translate failures into exit codes;
- emit action signals to terminal/logging/tracing;
- create tracing context when `--trace` is enabled.

It must not contain application/domain logic. Product capabilities must remain callable independently from ORC so the same functions can be used by the UI, APIs, tests, and future adapters.

The `uv`/ORC boundary is explicit: `uv` bootstraps and synchronises the Python environment; ORC operates once that environment exists.

## CLI conventions

- Interactive output is coloured by default when the terminal supports it.
- `--no-color` disables colour; `--color` can force it when appropriate.
- `--trace` is available from the first ORC version.
- Rich is the terminal presentation layer.
- Typer is the command and option layer.
- Action signals provide a common start/success/warning/failure vocabulary and can fan out to terminal output, logs, and trace events.

## Migration / implementation

The migration is deliberately incremental.

1. Work on `refactor/orchestration_simplification`, based on `dev`.
2. Keep the current Makefile working while ORC is developed.
3. Add a visible yellow Make warning pointing developers to this ACR and the ORC migration.
4. Establish the ACR method and expose ACRs through ORC.
5. Recreate the existing Make command categories and orchestration level in ORC.
6. Add a first-class development-session setup command.
7. Start using ORC as the preferred interface while Make remains a compatibility path.
8. Remove Make only after ORC has reached behavioural parity and has been used successfully for normal development.

## Initial command categories

ORC should preserve the intent of the current Make help categories:

- Environment
- Development
- Build / clean
- Testing / metrics
- Docker Compose
- Observability verification
- Observability UI access
- Maintenance

The command names may be reorganised into subcommands instead of preserving the flat Make target namespace.

## Consequences

### Positive

- orchestration becomes normal typed Python instead of increasingly complex Make/shell recipes;
- orchestration helpers can be unit-tested;
- Rich provides consistent terminal UX, progress bars, spinners, colour, and structured status output;
- Typer provides discoverable subcommands and typed parameters;
- tracing and action-signal emission are easier to standardise;
- platform-specific behaviour can be isolated behind explicit functions;
- application functions remain reusable by UI and tests rather than being trapped behind shell commands.

### Negative

- there is temporary duplication while Make and ORC coexist;
- ORC adds Python code and tests for operations that were previously expressed in recipes;
- the project must become an installable Python package for `[project.scripts]` to work reliably;
- parity must be checked before the Makefile can be deleted.

These costs are accepted because the existing Makefile has already crossed the threshold where further procedural orchestration is cheaper to maintain in Python.

## Exit / rollback criteria

The migration is considered complete when:

- every still-relevant Make category has an ORC equivalent;
- the normal development-session setup is available through ORC;
- ORC is used successfully for day-to-day development;
- tests cover the orchestration helpers that contain branching or expected-output checks;
- the Makefile is no longer required as a fallback.

At that point a follow-up ACR or an update to this record may authorise removal of the Makefile.

If ORC proves materially worse, Make remains intact during the migration and can continue to serve as the fallback without reconstructing the old workflow.
