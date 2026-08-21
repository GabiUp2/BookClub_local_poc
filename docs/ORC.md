# ORC — Book Club orchestration CLI

ORC is the preferred Python orchestration interface introduced by [ACR-0001](architecture/acr/ACR-0001-python-orchestration-orc.md).

The migration is intentionally non-destructive: the Makefile remains a compatibility interface until ORC has behavioural parity and has been used successfully in normal development.

## Bootstrap boundary

`uv` owns bootstrap and dependency synchronisation. ORC assumes the Python environment can already run it.

```bash
uv lock
uv sync --all-groups
uv run orc --help
```

After installation/sync, the console script is registered through `pyproject.toml`, so `orc` is also available from an activated environment.

## Global behaviour

```text
orc [--color|--no-color] [--trace] [-v|--verbose] [-q|--quiet] COMMAND ...
```

- Colour is automatic by default and can be forced on or off.
- `--trace` creates ORC OpenTelemetry spans and exports them to `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Every orchestration action emits an action signal:
  - terminal state (`start`, `success`, `warning`, `failure`, `info`);
  - structured action log in `logs/orc.log` by default;
  - Prometheus counters and duration histograms, pushed best-effort to `PUSHGATEWAY_URL`;
  - an `orc.action.signal` trace event when a trace is active.
- Telemetry failure must not make a successful orchestration command fail.

## Command categories

The first migration milestone keeps the same intent as the current Make categories while replacing the flat target namespace with subcommands.

| Make category / target | ORC |
| --- | --- |
| setup/environment | `orc env ...` |
| `venv` | `orc env venv` |
| `deps-seed` | `orc env deps-seed` |
| `lock` | `orc env lock` |
| `install` | `orc env install` |
| `install-dev` / `setup` | `orc env install-dev` / `orc env setup` |
| `sync` / `sync-dev` | `orc env sync` / `orc env sync-dev` |
| development | `orc dev ...` |
| `run` | `orc dev run` |
| `test` | `orc dev test` |
| `coverage` | `orc dev coverage` |
| `lint` | `orc dev lint` |
| `fmt` | `orc dev format` |
| `typecheck` | `orc dev typecheck` |
| `precommit` | `orc dev precommit` |
| build/clean | `orc build ...` |
| `clean` | `orc build clean` |
| `dist` | `orc build dist` |
| testing/metrics | `orc test-metrics ...` |
| `push-tests` | `orc test-metrics push` |
| `verify-test-metrics` | `orc test-metrics verify` |
| `test-cleanup-behavior` | `orc test-metrics cleanup-behavior` |
| Docker Compose | `orc compose ...` |
| `compose-install` | `orc compose install` |
| `compose-version` | `orc compose version` |
| `compose-switch` | `orc compose switch` |
| observability verification | `orc obs ...` |
| `verify-observability` | `orc obs verify` |
| `verify-quick` | `orc obs quick` |
| `verify-logs` | `orc obs logs` |
| `verify-integration` | `orc obs integration` |
| observability UI | `orc obs open --browser firefox|chrome` |
| maintenance | `orc maintenance ...` |
| `purge-old-data` | `orc maintenance purge-old-data` |

`ensure-uv` is intentionally not migrated: installing `uv` belongs on the bootstrap side of the uv/ORC boundary.

## Development session

`orc dev session` is the first orchestration that goes beyond direct Make parity.

It:

1. records the current branch and commit;
2. starts the Docker Compose stack;
3. waits for backend, frontend, Grafana, Prometheus, Loki and Pushgateway readiness;
4. optionally opens the development/observability URLs;
5. prints the useful local endpoints and emits a ready signal.

Examples:

```bash
orc dev session
orc --trace dev session
orc --trace dev session --browser firefox
```

## Architectural boundary

Code under `book_club.orc` may contain CLI parsing, presentation, external-process invocation, pre-flight checks, expected-output checks, and CLI-specific sequencing.

It must not contain Book Club product logic. When a workflow becomes product behaviour rather than developer orchestration, move it to an application/domain function and call that function from ORC, the UI/API, and tests.

## Migration completion

Do not delete the Makefile merely because an ORC command exists. Remove it only after the parity commands are exercised in real development and the exit criteria in ACR-0001 are satisfied.
