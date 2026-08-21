# Architecture Change Records (ACR)

Architecture Change Records capture decisions that materially change how this project is built, operated, tested, or maintained.

## When to write an ACR

Create an ACR before, or together with, a change that alters one or more of:

- project architecture or component boundaries;
- orchestration, build, packaging, deployment, or development workflows;
- persistence or data ownership;
- observability contracts;
- externally visible interfaces or long-lived developer conventions.

Do not use an ACR for ordinary bug fixes, local refactors that preserve architectural behaviour, or temporary experiments.

## Numbering and location

Records live in `docs/architecture/acr/` and use a monotonically increasing four-digit identifier:

```text
ACR-0001-short-decision-name.md
ACR-0002-another-decision.md
```

The identifier never changes, even if the record is later superseded.

## Status

Use one of:

- `Proposed`
- `Accepted`
- `Superseded by ACR-NNNN`
- `Rejected`
- `Deprecated`

## Required structure

```markdown
# ACR-NNNN — Decision title

- Status: Proposed | Accepted | Superseded | Rejected | Deprecated
- Date: YYYY-MM-DD
- Owners: ...

## Context
Why the decision is needed now.

## Decision
What we decided.

## Consequences
Positive and negative consequences we deliberately accept.

## Migration / implementation
How the change is introduced without destabilising the project.

## Exit / rollback criteria
How the decision can be reversed, replaced, or considered complete.
```

## Repository convention

When a legacy mechanism is intentionally kept during a migration, it should point at the ACR that explains why it is being replaced. The preferred developer-facing access is through `orc acr list` and `orc acr show <number>` once ORC is available.

An ACR records the decision; it does not replace implementation documentation or tests.
