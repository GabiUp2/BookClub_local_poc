import os
import sys
import re
import time
import json
import logging
import pytest
import subprocess

from pathlib import Path
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Add project `src/` to sys.path for tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.is_dir() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from book_club.observability.GitHandler import git_commit_and_branch

_SANITISE = re.compile(r"[^a-zA-Z0-9_.:-]")  # safe for Prom labels

# Session-wide registry and gauges for collecting all test metrics
_session_registry = None
_session_gauge = None
_session_outcome_gauge = None
_build_info_gauge = None

# Logger for sending test failures to Loki via Alloy
_loki_logger = None

_git_info = None

def _get_git_info():
    global _git_info
    if _git_info is None:
        try:
            _git_info = git_commit_and_branch()
        except Exception:
            _git_info = {"commit": "unknown", "short": "unknown", "ref": "unknown"}
    return _git_info

def _get_loki_logger():
    """Lazy-init logger that writes test failures to file for Alloy ingestion."""
    global _loki_logger
    if _loki_logger is None:
        _loki_logger = logging.getLogger("pytest.failures")
        _loki_logger.setLevel(logging.ERROR)
        
        # Write to logs/ directory for Alloy ingestion
        # (host: ./logs/ -> container: /development_logs/ via docker-compose volume)
        log_dir = PROJECT_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "pytest_failures.log"
        
        # File handler for Alloy to pick up
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.ERROR)
        # Simple format - one JSON object per line
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        _loki_logger.addHandler(file_handler)
        
        # Also to stderr for immediate visibility
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        _loki_logger.addHandler(console_handler)
        
        _loki_logger.propagate = False
    return _loki_logger

def _norm(value: str) -> str:
    return _SANITISE.sub("_", value or "unknown")

def pytest_collection_modifyitems(config, items):
    """Separate serial tests from parallel tests for xdist."""
    # When using xdist, we want serial tests to not be distributed
    # The --dist loadscope option + having all serial tests in the same file 
    # ensures they run on a single worker sequentially
    pass

def pytest_addoption(parser):
    g = parser.getgroup("prometheus")
    g.addoption(
        "--pushgw",
        action="store",
        default=os.getenv("PUSHGATEWAY_URL", "http://localhost:9091"),
        help="Pushgateway base URL (e.g. http://localhost:9091)",
    )
    g.addoption(
        "--prom-job",
        action="store",
        default=os.getenv("PROM_JOB", "pytest"),
        help="Prometheus job label for grouping in Pushgateway",
    )
    g.addoption(
        "--prom-instance",
        action="store",
        default=os.getenv("PROM_INSTANCE", os.uname().nodename if hasattr(os, "uname") else "local"),
        help="Prometheus instance label for grouping in Pushgateway",
    )
    g.addoption(
        "--prom-tags",
        action="store",
        default=os.getenv("PROM_EXTRA_TAGS", ""),
        help="Extra comma-separated tags to include as 'tags' label (optional)",
    )
    g.addoption(
        "--prom-cleanup",
        action="store",
        default=os.getenv("PROM_CLEANUP", "after"),
        choices=["before", "after", "both", "none"],
        help="When to delete old metrics from Pushgateway: before, after (default), both, or none",
    )

def pytest_sessionstart(session):
    """Clean up old metrics from Pushgateway before test run if configured."""
    cfg = session.config
    cleanup = cfg.getoption("--prom-cleanup")
    
    if cleanup in ("before", "both"):
        _cleanup_pushgateway(cfg)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    start = time.perf_counter()
    outcome = yield
    duration = time.perf_counter() - start
    
    # Collect metrics
    _collect_test_metric(item, duration, outcome)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test outcomes and log failures to Loki."""
    outcome = yield
    report = outcome.get_result()
    
    # Only process test call phase (not setup/teardown)
    if report.when == "call" and report.failed:
        _log_test_failure(item, report)

def _get_marker_arg(item, marker_name: str):
    m = item.get_closest_marker(marker_name)
    if not m:
        return None
    # Allow @pytest.mark.test_type("unit") or @pytest.mark.expected_duration("short")
    if m.args:
        return str(m.args[0])
    if m.kwargs and "name" in m.kwargs:
        return str(m.kwargs["name"])
    return None

def _log_test_failure(item, report):
    """Log test failure details to file for Alloy/Loki ingestion."""
    logger = _get_loki_logger()
    
    # Extract failure information
    nodeid = item.nodeid
    file_path = nodeid.split("::", 1)[0] if "::" in nodeid else nodeid
    
    # Get the failure message and traceback
    failure_msg = str(report.longrepr) if report.longrepr else "No failure details"
    
    # Extract short error for quick viewing
    short_error = failure_msg.split('\n')[-1] if '\n' in failure_msg else failure_msg
    
    # Create structured log entry with timestamp
    import datetime
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": "ERROR",
        "event": "test_failure",
        "source": "pytest",
        "test_name": nodeid,
        "file": file_path,
        "outcome": report.outcome,
        "duration": report.duration if hasattr(report, 'duration') else 0,
        "short_error": short_error[:200],
        "failure_message": failure_msg[:2000],  # Truncate very long messages
        "test_type": _get_marker_arg(item, "test_type") or "unspecified",
    }
    
    # Log as JSON (one line per failure)
    logger.error(json.dumps(log_entry))

def _collect_test_metric(item, duration: float, outcome):
    """Collect test metric into session-wide registry for batch push at end."""
    global _session_registry, _session_gauge, _session_outcome_gauge
    
    cfg = item.config
    extra_tags_raw = cfg.getoption("--prom-tags")

    # Lazy initialization of session-wide registry and gauges
    if _session_registry is None:
        _session_registry = CollectorRegistry()
        _session_gauge = Gauge(
            "test_duration_seconds",
            "Pytest test execution time",
            labelnames=("test_name", "file", "type", "expected_duration", "tags", "outcome"),
            registry=_session_registry,
        )
        _session_outcome_gauge = Gauge(
            "test_outcome",
            "Test outcome: 1=passed, 0=failed",
            labelnames=("test_name", "file", "type", "expected_duration", "tags"),
            registry=_session_registry,
        )
        # Initialise build_info once per session
        gi = _get_git_info()
        repo_name = PROJECT_ROOT.name
        branch = gi.get("ref", "unknown")
        commit = gi.get("short") or gi.get("commit", "unknown")
        global _build_info_gauge
        _build_info_gauge = Gauge(
            "build_info",
            "Repository build information",
            labelnames=("repo", "branch", "commit"),
            registry=_session_registry,
        )
        _build_info_gauge.labels(
            _norm(repo_name)[:100],
            _norm(branch)[:100],
            _norm(commit)[:100],
        ).set(1)

    # Labels
    nodeid = item.nodeid  # e.g. tests/mod/test_x.py::TestCls::test_foo[param]
    file_path = nodeid.split("::", 1)[0]
    test_name = nodeid

    test_type = _get_marker_arg(item, "test_type") or "unspecified"
    expected_duration = _get_marker_arg(item, "expected_duration") or "unspecified"

    # Optional extra freeform tags from CLI/env (comma separated)
    tags = ",".join(
        t.strip() for t in (extra_tags_raw.split(",") if extra_tags_raw else []) if t.strip()
    ) or "none"

    # Determine outcome from the call result
    test_passed = not (outcome and hasattr(outcome, 'excinfo') and outcome.excinfo)
    outcome_str = "passed" if test_passed else "failed"
    
    # Add this test's metric to the session-wide gauges
    # Be mindful of cardinality—normalise and keep strings compact
    _session_gauge.labels(
        test_name=_norm(test_name)[:250], # max 250 chars
        file=_norm(file_path)[:200], # max 200 chars
        type=_norm(test_type),
        expected_duration=_norm(expected_duration),
        tags=_norm(tags)[:120], # max 120 chars
        outcome=outcome_str,
    ).set(duration)
    
    _session_outcome_gauge.labels(
        test_name=_norm(test_name)[:250], # max 250 chars
        file=_norm(file_path)[:200], # max 200 chars
        type=_norm(test_type),
        expected_duration=_norm(expected_duration),
        tags=_norm(tags)[:120], # max 120 chars
    ).set(1 if test_passed else 0)

def pytest_sessionfinish(session, exitstatus):
    """Push all collected test metrics to Pushgateway at session end."""
    global _session_registry, _session_gauge
    
    if _session_registry is None:
        return  # No tests ran
    
    cfg = session.config
    pushgw = cfg.getoption("--pushgw")
    job = cfg.getoption("--prom-job")
    instance = cfg.getoption("--prom-instance")
    cleanup = cfg.getoption("--prom-cleanup")
    
    # If running with pytest-xdist, include worker ID to avoid overwrites
    worker_id = getattr(cfg, "workerinput", {}).get("workerid", "main")
    instance_with_worker = f"{instance}_{worker_id}" if worker_id != "main" else instance
    
    gi = _get_git_info()
    branch = gi.get("ref", "unknown")
    grouping_key = {"instance": _norm(instance_with_worker), "branch": _norm(branch)}
    try:
        push_to_gateway(pushgw, job=_norm(job), registry=_session_registry, grouping_key=grouping_key, timeout=5.0)
    except Exception as e:
        try:
            # retry without branch if gateway rejects grouping key
            push_to_gateway(pushgw, job=_norm(job), registry=_session_registry, grouping_key={"instance": _norm(instance_with_worker)}, timeout=5.0)
        except Exception as e2:
            import warnings
            warnings.warn(f"Pushgateway push failed: {e2}", UserWarning)
    
    # Clean up after push if configured
    if cleanup in ("after", "both"):
        _cleanup_pushgateway(cfg)

def _cleanup_pushgateway(cfg):
    """Delete all metrics for this job from Pushgateway."""
    import urllib.request
    import urllib.error
    from urllib.parse import quote
    import json
    
    pushgw = cfg.getoption("--pushgw")
    job = cfg.getoption("--prom-job")
    normalized_job = _norm(job)
    
    try:
        # Query API to find all metric groups for this job
        api_url = f"{pushgw}/api/v1/metrics"
        with urllib.request.urlopen(api_url, timeout=5.0) as response:
            data = json.loads(response.read().decode())
            groups = [g for g in data.get("data", []) if g.get("labels", {}).get("job") == normalized_job]
        
        # Delete each metric group by its full grouping key
        for group in groups:
            labels = group.get("labels", {})
            # Build DELETE URL: /metrics/job/<job>/instance/<instance>/...
            url_parts = [f"{pushgw}/metrics/job/{normalized_job}"]
            for key, value in labels.items():
                if key != "job":  # job is already in the path
                    url_parts.append(f"/{key}/{quote(value, safe='')}")
            delete_url = "".join(url_parts)
            
            req = urllib.request.Request(delete_url, method="DELETE")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                resp.read()
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # No metrics to delete, that's fine
            pass
        else:
            import warnings
            warnings.warn(f"Pushgateway cleanup failed: HTTP {e.code}", UserWarning)
    except Exception as e:
        # Cleanup failures are non-fatal
        import warnings
        warnings.warn(f"Pushgateway cleanup failed: {e}", UserWarning)

@pytest.fixture(scope="session")
def docker_prefix() -> list[str]:
    """Determine how to invoke Docker.

    - Prefer direct `docker` if accessible.
    - Fallback to passwordless sudo (`sudo -n docker`) if configured.
    - Skip integration tests if neither works without prompting for a password.
    """
    def can_run(cmd: list[str]) -> bool:
        return (
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode
            == 0
        )

    if can_run(["docker", "compose", "ps"]):
        return []

    if can_run(["sudo", "-n", "docker", "compose", "ps"]):
        return ["sudo", "-n"]

    pytest.skip(
        "Docker daemon not accessible without sudo and passwordless sudo not configured. "
        "Skip integration tests or configure user in the docker group / NOPASSWD sudo."
    )
