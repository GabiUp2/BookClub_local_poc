from __future__ import annotations

import glob
import os
import shutil
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Annotated

import httpx
import typer
from opentelemetry import trace
from rich.markdown import Markdown
from rich.table import Table

from book_club.orc.runner import CommandFailed, run
from book_club.orc.runtime import (
    OrcRuntime,
    configure_action_logger,
    configure_tracing,
    make_console,
)


app = typer.Typer(
    name="orc",
    help="Book Club orchestration CLI. Thin wrapper; no application logic belongs here.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
env_app = typer.Typer(help="Environment and dependency operations.")
dev_app = typer.Typer(help="Development commands and development-session setup.")
build_app = typer.Typer(help="Build and clean operations.")
test_metrics_app = typer.Typer(help="Test metrics and Pushgateway verification.")
compose_app = typer.Typer(help="Docker Compose installation and inspection.")
obs_app = typer.Typer(help="Observability verification and UI access.")
maintenance_app = typer.Typer(help="Destructive and housekeeping operations.")
acr_app = typer.Typer(help="Architecture Change Records.")

app.add_typer(env_app, name="env")
app.add_typer(dev_app, name="dev")
app.add_typer(build_app, name="build")
app.add_typer(test_metrics_app, name="test-metrics")
app.add_typer(compose_app, name="compose")
app.add_typer(obs_app, name="obs")
app.add_typer(maintenance_app, name="maintenance")
app.add_typer(acr_app, name="acr")


class Browser(str, Enum):
    none = "none"
    firefox = "firefox"
    chrome = "chrome"


def _runtime(ctx: typer.Context) -> OrcRuntime:
    root = ctx.find_root()
    runtime = root.obj
    if not isinstance(runtime, OrcRuntime):
        raise RuntimeError("ORC runtime was not initialised")
    return runtime


def _uv() -> str:
    return shutil.which("uv") or str(Path.home() / ".local/bin/uv")


def _git_value(runtime: OrcRuntime, *args: str, default: str = "unknown") -> str:
    result = run(
        runtime,
        "git.metadata",
        "Reading git metadata",
        ["git", *args],
        capture=True,
        check=False,
    )
    value = result.stdout.strip()
    return value or default


def _wait_http(
    runtime: OrcRuntime,
    action: str,
    description: str,
    url: str,
    *,
    timeout: float = 60.0,
    headers: dict[str, str] | None = None,
) -> None:
    deadline = time.monotonic() + timeout
    with runtime.action(action, description):
        with runtime.console.status(f"[cyan]{description}[/cyan]"):
            while time.monotonic() < deadline:
                try:
                    response = httpx.get(url, headers=headers, timeout=2.0)
                    if response.is_success:
                        return
                except httpx.HTTPError:
                    pass
                time.sleep(1.0)
    raise RuntimeError(f"Timed out waiting for {url}")


def _check_http(
    runtime: OrcRuntime,
    action: str,
    description: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    expected_text: str | None = None,
) -> httpx.Response:
    with runtime.action(action, description):
        response = httpx.get(url, headers=headers, timeout=5.0)
        response.raise_for_status()
        if expected_text is not None and expected_text not in response.text:
            raise RuntimeError(f"Expected {expected_text!r} in response from {url}")
        return response


def _open_observability(runtime: OrcRuntime, browser: Browser) -> None:
    if browser is Browser.none:
        return

    urls = [
        "http://localhost:8000/",
        "http://localhost:3000",
        "http://localhost:9090",
        "http://localhost:3100",
        "http://localhost:9091",
    ]
    exe = "firefox.exe" if browser is Browser.firefox else "chrome.exe"
    standard_paths = (
        [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]
        if browser is Browser.firefox
        else [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    )
    url_literal = ",".join(f'\"{url}\"' for url in urls)
    path_literal = ",".join(f'\"{path}\"' for path in standard_paths)
    flag = "-new-tab" if browser is Browser.firefox else "--new-tab"
    script = (
        f'$urls=@({url_literal}); '
        f'$paths=@({path_literal}); '
        f'$browser=(Get-Command {exe} -ErrorAction SilentlyContinue).Source; '
        '$proc=Get-Process '
        f'{browser.value} -ErrorAction SilentlyContinue | Select-Object -First 1; '
        'if (-not $browser -and $proc) {$browser=$proc.Path}; '
        'if (-not $browser) {foreach ($path in $paths) {if (Test-Path $path) {$browser=$path; break}}}; '
        'if (-not $browser) {Write-Error "Browser not found"; exit 1}; '
        f'Start-Process -FilePath $browser -ArgumentList ($urls | ForEach-Object {{"{flag}", $_}})'
    )
    run(
        runtime,
        "obs.open",
        f"Opening observability URLs in {browser.value}",
        ["powershell.exe", "-NoLogo", "-NoProfile", "-Command", script],
    )


def _service_table() -> Table:
    table = Table(title="Book Club development session")
    table.add_column("Service")
    table.add_column("URL")
    table.add_row("Frontend", "http://localhost:8000/")
    table.add_row("Backend", "http://localhost:8010/health")
    table.add_row("Grafana", "http://localhost:3000")
    table.add_row("Prometheus", "http://localhost:9090")
    table.add_row("Loki", "http://localhost:3100")
    table.add_row("Pushgateway", "http://localhost:9091")
    table.add_row("Tempo", "http://localhost:3200")
    table.add_row("Qdrant", "http://localhost:6333")
    return table


@app.callback()
def main(
    ctx: typer.Context,
    color: Annotated[
        bool | None,
        typer.Option(
            "--color/--no-color",
            help="Force colour on/off. Default: auto-detect terminal capability.",
        ),
    ] = None,
    trace_enabled: Annotated[
        bool,
        typer.Option("--trace", help="Emit ORC OpenTelemetry spans to the configured OTLP endpoint."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show executed external commands and action logs."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress non-warning action output."),
    ] = False,
) -> None:
    if verbose and quiet:
        raise typer.BadParameter("--verbose and --quiet are mutually exclusive")

    configure_tracing(trace_enabled)
    runtime = OrcRuntime(
        console=make_console(color),
        trace_enabled=trace_enabled,
        verbose=verbose,
        quiet=quiet,
        logger=configure_action_logger(verbose),
    )
    ctx.obj = runtime

    if trace_enabled:
        tracer = trace.get_tracer("book_club.orc")
        span_manager = tracer.start_as_current_span(
            "orc.command",
            attributes={"process.command_line": " ".join(sys.argv)},
        )
        span_manager.__enter__()
        ctx.call_on_close(lambda: span_manager.__exit__(None, None, None))


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


@env_app.command("venv")
def env_venv(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "env.venv", "Creating/updating .venv with Python 3.11", [_uv(), "venv", ".venv", "--python", "3.11"])


@env_app.command("deps-seed")
def env_deps_seed(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    with runtime.action("env.deps-seed", "Creating legacy requirements seed files when absent"):
        requirements = Path("requirements.in")
        requirements_dev = Path("requirements-dev.in")
        if not requirements.exists():
            requirements.write_text("httpx>=0.27.0\npydantic>=2.8.0\nrich>=13.7.0\n", encoding="utf-8")
        if not requirements_dev.exists():
            requirements_dev.write_text(
                "pytest>=8.2.0\npytest-cov>=5.0.0\nruff>=0.6.0\nmypy>=1.11.0\npre-commit>=3.7.0\n",
                encoding="utf-8",
            )


@env_app.command("lock")
def env_lock(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "env.lock", "Resolving project lockfile", [_uv(), "lock"])


@env_app.command("sync")
def env_sync(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "env.sync", "Synchronising runtime dependencies", [_uv(), "sync"])


@env_app.command("sync-dev")
def env_sync_dev(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "env.sync-dev", "Synchronising runtime and development dependencies", [_uv(), "sync", "--all-groups"])


def _install_precommit(runtime: OrcRuntime) -> None:
    run(
        runtime,
        "env.precommit-install",
        "Installing pre-commit hooks",
        [_uv(), "run", "pre-commit", "install"],
        check=False,
    )


@env_app.command("install")
def env_install(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    env_venv(ctx)
    env_lock(ctx)
    env_sync(ctx)
    _install_precommit(runtime)


@env_app.command("install-dev")
def env_install_dev(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    env_venv(ctx)
    env_lock(ctx)
    env_sync_dev(ctx)
    _install_precommit(runtime)


@env_app.command("setup")
def env_setup(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    env_install_dev(ctx)
    runtime.emit("success", "env.setup", "uv development environment is ready")


# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------


@dev_app.command("run")
def dev_run(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(
        runtime,
        "dev.run",
        "Running Book Club application",
        [_uv(), "run", "-m", "book_club.__main__"],
        env={"GRAFANA_URL": os.environ.get("GRAFANA_URL", "http://athena:3000")},
    )


@dev_app.command("test")
def dev_test(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "dev.test", "Running test suite", [_uv(), "run", "-m", "pytest", "-q"], env={"PYTHONPATH": "src"})


@dev_app.command("coverage")
def dev_coverage(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(
        runtime,
        "dev.coverage",
        "Running tests with coverage",
        [_uv(), "run", "-m", "pytest", "--cov=src", "--cov-report=term-missing"],
        env={"PYTHONPATH": "src"},
    )


@dev_app.command("lint")
def dev_lint(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "dev.lint", "Linting repository with Ruff", [_uv(), "run", "ruff", "check", "."])


@dev_app.command("format")
def dev_format(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "dev.format-fix", "Applying Ruff fixes", [_uv(), "run", "ruff", "check", "--fix", "."])
    run(runtime, "dev.format", "Formatting repository with Ruff", [_uv(), "run", "ruff", "format", "."])


@dev_app.command("typecheck")
def dev_typecheck(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "dev.typecheck", "Type-checking src with mypy", [_uv(), "run", "mypy", "src"])


@dev_app.command("precommit")
def dev_precommit(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "dev.precommit", "Running pre-commit on all files", [_uv(), "run", "pre-commit", "run", "--all-files"])


@dev_app.command("session")
def dev_session(
    ctx: typer.Context,
    browser: Annotated[
        Browser,
        typer.Option("--browser", help="Optionally open development/observability tabs."),
    ] = Browser.none,
) -> None:
    """Bring up the normal local development stack and verify it before coding."""
    runtime = _runtime(ctx)
    branch = _git_value(runtime, "branch", "--show-current")
    commit = _git_value(runtime, "rev-parse", "--short", "HEAD")
    runtime.emit("info", "dev.session", f"Starting session on {branch}@{commit}")

    run(runtime, "dev.session.compose", "Starting Docker Compose development stack", ["docker", "compose", "up", "-d"])
    _wait_http(runtime, "dev.session.backend", "Waiting for backend health", "http://localhost:8010/health", timeout=120)
    _wait_http(runtime, "dev.session.frontend", "Waiting for frontend", "http://localhost:8000/", timeout=180)
    _wait_http(runtime, "dev.session.grafana", "Waiting for Grafana", "http://localhost:3000/api/health", timeout=90)
    _wait_http(runtime, "dev.session.prometheus", "Waiting for Prometheus", "http://localhost:9090/-/ready", timeout=90)
    _wait_http(
        runtime,
        "dev.session.loki",
        "Waiting for Loki",
        "http://localhost:3100/ready",
        timeout=90,
        headers={"X-Scope-OrgID": "local"},
    )
    _wait_http(runtime, "dev.session.pushgateway", "Waiting for Pushgateway", "http://localhost:9091/-/ready", timeout=90)
    _open_observability(runtime, browser)
    runtime.console.print(_service_table())
    runtime.emit("success", "dev.session", f"Development session ready on {branch}@{commit}")


# ---------------------------------------------------------------------------
# Build / clean
# ---------------------------------------------------------------------------


@build_app.command("clean")
def build_clean(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    with runtime.action("build.clean", "Removing local build and tool caches"):
        for path in [".venv", ".pytest_cache", ".mypy_cache", "dist", "build"]:
            shutil.rmtree(path, ignore_errors=True)
        for path in glob.glob("*.egg-info"):
            shutil.rmtree(path, ignore_errors=True)


@build_app.command("dist")
def build_dist(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "build.dist", "Building source and wheel distributions", [_uv(), "build"])


# ---------------------------------------------------------------------------
# Testing / metrics
# ---------------------------------------------------------------------------


@test_metrics_app.command("push")
def test_metrics_push(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    branch = _git_value(runtime, "branch", "--show-current")
    run(
        runtime,
        "test-metrics.push",
        "Running tests and pushing metrics to Pushgateway",
        [
            _uv(),
            "run",
            "pytest",
            "--pushgw=http://localhost:9091",
            "--prom-job=pytest",
            "--prom-instance=dev",
            f"--prom-tags=branch={branch},run_id=local",
            "--prom-cleanup=none",
        ],
    )


@test_metrics_app.command("cleanup-behavior")
def test_metrics_cleanup_behavior(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(
        runtime,
        "test-metrics.cleanup-behavior",
        "Testing all Pushgateway cleanup behaviours",
        [
            _uv(),
            "run",
            "pytest",
            "tests/observability/test_pushgateway_cleanup.py",
            "-p",
            "no:xdist",
            "-o",
            "addopts=",
            "-v",
        ],
    )


@test_metrics_app.command("verify")
def test_metrics_verify(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    result = run(
        runtime,
        "test-metrics.verify.test",
        "Executing verification test and pushing its metrics",
        [
            _uv(),
            "run",
            "pytest",
            "tests/observability/test_monitoring.py::test_server_health_endpoint",
            "-p",
            "no:xdist",
            "-o",
            "addopts=",
            "--pushgw=http://localhost:9091",
            "--prom-job=pytest_verify",
            "--prom-instance=verify",
            "--prom-cleanup=none",
            "-q",
        ],
        capture=True,
    )
    if "1 passed" not in result.stdout:
        raise RuntimeError("Verification pytest invocation did not report '1 passed'")

    time.sleep(1)
    pushgateway = _check_http(
        runtime,
        "test-metrics.verify.pushgateway",
        "Checking verification metrics in Pushgateway",
        "http://localhost:9091/metrics",
    )
    if 'job="pytest_verify"' not in pushgateway.text or "test_duration_seconds{" not in pushgateway.text:
        raise RuntimeError("Verification metrics were not found in Pushgateway")

    targets = _check_http(
        runtime,
        "test-metrics.verify.prom-target",
        "Checking Prometheus Pushgateway target",
        "http://localhost:9090/api/v1/targets",
    ).json()
    active_targets = targets.get("data", {}).get("activeTargets", [])
    matching_targets = [
        target
        for target in active_targets
        if "pushgateway" in target.get("scrapePool", "").lower()
        or "pushgateway" in str(target.get("labels", {})).lower()
    ]
    if not matching_targets or matching_targets[0].get("health") != "up":
        raise RuntimeError("Prometheus is not scraping Pushgateway successfully")

    time.sleep(2)
    query = httpx.get(
        "http://localhost:9090/api/v1/query",
        params={"query": 'test_duration_seconds{job="pytest_verify"}'},
        timeout=5.0,
    )
    query.raise_for_status()
    count = len(query.json().get("data", {}).get("result", []))
    if count == 0:
        runtime.emit("warning", "test-metrics.verify.prometheus", "Metrics have not reached Prometheus yet; scrape interval may not have elapsed")
    else:
        runtime.emit("success", "test-metrics.verify.prometheus", f"Found {count} verification metric series in Prometheus")

    run(
        runtime,
        "test-metrics.verify.cleanup-test",
        "Testing Pushgateway cleanup-before behaviour",
        [_uv(), "run", "pytest", "tests/observability/test_pushgateway_cleanup.py::test_cleanup_before_prevents_accumulation", "-q"],
    )
    for job in ("pytest_verify", "pytest_cleanup_validation"):
        httpx.delete(f"http://localhost:9091/metrics/job/{job}", timeout=5.0)
    runtime.emit("success", "test-metrics.verify", "Test metrics pipeline verification complete")


# ---------------------------------------------------------------------------
# Docker Compose
# ---------------------------------------------------------------------------


@compose_app.command("version")
def compose_version(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "compose.version", "Reading Docker Compose version", ["docker", "compose", "version"], check=False)


@compose_app.command("switch")
def compose_switch(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(
        runtime,
        "compose.switch",
        "Installing docker-compose-switch",
        ["sudo", "apt", "install", "-y", "docker-compose-switch"],
        check=False,
    )


@compose_app.command("install")
def compose_install(
    ctx: typer.Context,
    version: Annotated[str, typer.Option("--version")] = "v2.29.2",
) -> None:
    runtime = _runtime(ctx)
    existing = run(
        runtime,
        "compose.detect",
        "Checking for Docker Compose v2",
        ["docker", "compose", "version"],
        capture=True,
        check=False,
    )
    if existing.returncode == 0:
        runtime.emit("success", "compose.install", "Docker Compose v2 is already installed")
        return

    if shutil.which("apt"):
        run(runtime, "compose.apt-update", "Updating APT metadata", ["sudo", "apt", "update"])
        run(
            runtime,
            "compose.apt-prereqs",
            "Installing Docker repository prerequisites",
            ["sudo", "apt", "install", "-y", "ca-certificates", "curl", "gnupg"],
        )
        run(runtime, "compose.keyring-dir", "Creating Docker APT keyring directory", ["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"])
        run(
            runtime,
            "compose.docker-packages",
            "Installing Docker Compose v2 packages",
            ["sudo", "apt", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"],
        )
    else:
        arch = os.uname().machine
        binary = {"x86_64": "docker-compose-linux-x86_64", "aarch64": "docker-compose-linux-aarch64", "arm64": "docker-compose-linux-aarch64"}.get(arch)
        if binary is None:
            raise RuntimeError(f"Unsupported architecture: {arch}")
        target_dir = Path.home() / ".docker" / "cli-plugins"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "docker-compose"
        url = f"https://github.com/docker/compose/releases/download/{version}/{binary}"
        with runtime.action("compose.download", f"Downloading Docker Compose {version}"):
            with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
                response.raise_for_status()
                with target.open("wb") as handle:
                    for chunk in response.iter_bytes():
                        handle.write(chunk)
            target.chmod(0o755)

    compose_version(ctx)


# ---------------------------------------------------------------------------
# Observability verification / UI
# ---------------------------------------------------------------------------


@obs_app.command("quick")
def obs_quick(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "obs.quick.services", "Checking observability containers", ["docker", "compose", "ps", "alloy", "loki", "grafana"], check=True)
    _check_http(runtime, "obs.quick.loki", "Checking Loki readiness", "http://localhost:3100/ready", headers={"X-Scope-OrgID": "local"})
    _check_http(runtime, "obs.quick.grafana", "Checking Grafana health", "http://localhost:3000/api/health")


@obs_app.command("logs")
def obs_logs(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    end_ns = int(time.time()) * 1_000_000_000
    start_ns = end_ns - 600_000_000_000
    with runtime.action("obs.logs", "Checking recent main.py logs in Loki"):
        response = httpx.get(
            "http://localhost:3100/loki/api/v1/query_range",
            headers={"X-Scope-OrgID": "local"},
            params={"query": '{filename="main.py"}', "start": str(start_ns), "end": str(end_ns)},
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json().get("data", {}).get("result", [])
        if not result:
            raise RuntimeError("No logs from main.py found in the last 10 minutes")
        runtime.console.print(f"Found {len(result)} Loki stream(s)")


@obs_app.command("verify")
def obs_verify(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(
        runtime,
        "obs.verify.services",
        "Checking observability services are running",
        ["docker", "compose", "ps", "alloy", "loki", "grafana", "prometheus"],
    )
    _check_http(runtime, "obs.verify.loki", "Checking Loki readiness", "http://localhost:3100/ready", headers={"X-Scope-OrgID": "local"})
    _check_http(runtime, "obs.verify.grafana", "Checking Grafana health", "http://localhost:3000/api/health")
    _check_http(runtime, "obs.verify.alloy", "Checking Alloy HTTP endpoint", "http://localhost:12345/")
    run(runtime, "obs.verify.generate-log", "Generating a development test log", [sys.executable, "main.py"])
    time.sleep(3)
    labels = _check_http(
        runtime,
        "obs.verify.loki-labels",
        "Checking that logs reached Loki",
        "http://localhost:3100/loki/api/v1/labels",
        headers={"X-Scope-OrgID": "local"},
    )
    if "filename" not in labels.text:
        raise RuntimeError("No filename label found in Loki")
    datasources = _check_http(runtime, "obs.verify.datasources", "Checking Grafana datasources", "http://localhost:3000/api/datasources")
    if "http://loki:3100" not in datasources.text:
        raise RuntimeError("Loki datasource is not configured in Grafana")


@obs_app.command("integration")
def obs_integration(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    run(runtime, "obs.integration.compose", "Bringing up complete stack", ["docker", "compose", "up", "-d"])
    _wait_http(runtime, "obs.integration.server", "Waiting for server", "http://localhost:8010/health", timeout=120)
    _wait_http(runtime, "obs.integration.app", "Waiting for frontend", "http://localhost:8000/", timeout=180)
    run(
        runtime,
        "obs.integration.internal-health",
        "Checking frontend-to-server connectivity inside Docker",
        ["docker", "compose", "exec", "-T", "bookclub-app", "wget", "-qO-", "http://bookclub-server:8010/health"],
    )
    _check_http(runtime, "obs.integration.metrics", "Checking server metrics endpoint", "http://localhost:8010/metrics")
    targets = _check_http(runtime, "obs.integration.prometheus", "Checking Prometheus targets", "http://localhost:9090/api/v1/targets").json()
    healthy_server = any(
        target.get("labels", {}).get("job") == "bookclub-server" and target.get("health") == "up"
        for target in targets.get("data", {}).get("activeTargets", [])
    )
    if not healthy_server:
        raise RuntimeError("Prometheus target bookclub-server is not up")
    _check_http(runtime, "obs.integration.loki", "Checking Loki readiness", "http://localhost:3100/ready", headers={"X-Scope-OrgID": "local"})
    _check_http(runtime, "obs.integration.grafana", "Checking Grafana health", "http://localhost:3000/api/health")
    runtime.emit("success", "obs.integration", "Integration verification complete")


@obs_app.command("open")
def obs_open(
    ctx: typer.Context,
    browser: Annotated[Browser, typer.Option("--browser")] = Browser.firefox,
) -> None:
    _open_observability(_runtime(ctx), browser)


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


@maintenance_app.command("purge-old-data")
def maintenance_purge_old_data(
    ctx: typer.Context,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    runtime = _runtime(ctx)
    runtime.emit("warning", "maintenance.purge", "This deletes local logs, metrics history, traces/vector data and Grafana session data; configuration and dashboards are kept")
    if not yes and not typer.confirm("Are you sure?", default=False):
        runtime.emit("warning", "maintenance.purge", "Purge cancelled")
        return

    run(
        runtime,
        "maintenance.purge.stop",
        "Stopping data-owning services",
        ["docker", "compose", "stop", "prometheus", "loki", "pushgateway", "qdrant", "grafana", "alloy"],
        check=False,
    )
    with runtime.action("maintenance.purge.files", "Removing persisted local observability/vector data"):
        for pattern in ["logs/*.log", "src/book_club/app/logs/*.log", "src/book_club/server/logs/*.log"]:
            for raw_path in glob.glob(pattern):
                Path(raw_path).unlink(missing_ok=True)
        for directory in ["observability/prometheus/data", "observability/loki/data", "data/qdrant"]:
            path = Path(directory)
            if path.exists():
                for child in path.iterdir():
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink(missing_ok=True)
        for raw_path in glob.glob("observability/grafana/data/grafana.db*"):
            Path(raw_path).unlink(missing_ok=True)

    run(
        runtime,
        "maintenance.purge.start",
        "Restarting cleaned services",
        ["docker", "compose", "up", "-d", "prometheus", "loki", "pushgateway", "qdrant", "grafana", "alloy"],
    )
    _wait_http(runtime, "maintenance.purge.prometheus", "Waiting for Prometheus", "http://localhost:9090/-/ready", timeout=90)
    _wait_http(runtime, "maintenance.purge.loki", "Waiting for Loki", "http://localhost:3100/ready", timeout=90, headers={"X-Scope-OrgID": "local"})
    _wait_http(runtime, "maintenance.purge.pushgateway", "Waiting for Pushgateway", "http://localhost:9091/-/ready", timeout=90)
    _wait_http(runtime, "maintenance.purge.grafana", "Waiting for Grafana", "http://localhost:3000/api/health", timeout=90)


# ---------------------------------------------------------------------------
# ACR
# ---------------------------------------------------------------------------


def _acr_files() -> list[Path]:
    return sorted(Path("docs/architecture/acr").glob("ACR-*.md"))


@acr_app.command("list")
def acr_list(ctx: typer.Context) -> None:
    runtime = _runtime(ctx)
    table = Table(title="Architecture Change Records")
    table.add_column("ACR")
    table.add_column("Title")
    for path in _acr_files():
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        title = first_line.removeprefix("# ")
        number = path.name.split("-", 2)[:2]
        table.add_row("-".join(number), title)
    runtime.console.print(table)


@acr_app.command("show")
def acr_show(ctx: typer.Context, number: int) -> None:
    runtime = _runtime(ctx)
    prefix = f"ACR-{number:04d}-"
    matches = [path for path in _acr_files() if path.name.startswith(prefix)]
    if not matches:
        raise typer.BadParameter(f"No {prefix}*.md record exists")
    runtime.console.print(Markdown(matches[0].read_text(encoding="utf-8")))


if __name__ == "__main__":
    app()
