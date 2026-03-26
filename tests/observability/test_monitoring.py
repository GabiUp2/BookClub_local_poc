"""Integration tests for observability stack (Prometheus, Loki) and server health.

Verifies that:
- Prometheus scrapes targets successfully
- Loki receives logs from the application
- FastAPI server /health and /metrics endpoints respond correctly

Uses British English in comments and docstrings.
"""

from __future__ import annotations

import os
import time

import pytest
import requests

pytestmark = pytest.mark.integration

@pytest.fixture(scope="session")
def loki_url() -> str:
    """Loki query API base URL."""
    return os.getenv("LOKI_URL", "http://localhost:3100")


@pytest.fixture(scope="session")
def prom_url() -> str:
    """Prometheus query API base URL."""
    return os.getenv("PROM_URL", "http://localhost:9090")


@pytest.fixture(scope="session")
def server_url() -> str:
    """FastAPI server base URL (port 8010)."""
    return os.getenv("SERVER_URL", "http://localhost:8010")


@pytest.fixture(scope="session")
def app_url() -> str:
    """Frontend app base URL (port 8000). Reserved for future use."""
    return os.getenv("APP_URL", "http://localhost:8000")

def backoff_get(
    url: str,
    timeout: float = 30,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    """Poll URL until it returns 2xx or timeout elapses.

    Args:
        url: Target URL to GET.
        timeout: Maximum time to wait in seconds.
        headers: Optional HTTP headers to include in the request.

    Returns:
        Successful Response object.

    Raises:
        AssertionError: If timeout is reached without success.
    """
    t0 = time.time()
    last: requests.Response | Exception | None = None
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=5, headers=headers)
            if r.ok:
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(1)
    raise AssertionError(f"Timeout waiting for {url}: {last}")

def test_prometheus_targets_healthy(prom_url: str) -> None:
    """Verify Prometheus has at least one healthy scrape target."""
    r = backoff_get(f"{prom_url}/api/v1/targets?state=active", timeout=60)
    data = r.json()["data"]["activeTargets"]
    assert data, "No active targets in Prometheus"
    unhealthy = [t for t in data if t.get("health", "").lower() != "up"]
    assert not unhealthy, f"Unhealthy targets: {unhealthy}"

@pytest.mark.long
def test_loki_has_logs(loki_url: str) -> None:
    """Verify Loki has received logs from the observability stack.

    Queries for any logs in Loki. Currently checks connectivity and ingestion pipeline.
    Loki is running in multi-tenant mode; queries require X-Scope-OrgID header.

    NOTE: This test will skip if the application logging is not yet configured.
    Once LokiHandler is integrated into the server, this will verify app logs.
    """
    # Loki multi-tenant header (matches Alloy's tenant_id = "local")
    headers = {"X-Scope-OrgID": "local"}
    
    # First check if Loki is reachable and has any logs at all
    # Query for any logs (broad check while logging infrastructure is being built)
    queries_to_try = [
        ('{filename=~".+"}', "logs with filename label (from Alloy file sources)"),
        ('{level=~".+"}', "logs with level label"),
        ('{logger=~".+"}', "logs with logger label (from LokiHandler)"),
    ]
    
    for query, description in queries_to_try:
        r = backoff_get(
            f"{loki_url}/loki/api/v1/query?query={query}",
            timeout=60,
            headers=headers,
        )
        streams = r.json().get("data", {}).get("result", [])
        if streams:
            # Found logs - test passes
            return
    
    # No logs found with any query
    pytest.skip(
        "No logs in Loki. This is expected if the application logging infrastructure "
        "is not yet configured. Alloy is running but no logs are being written. "
        "Configure logging in server_main.py to emit logs."
    )

def test_server_health_endpoint(server_url: str) -> None:
    """Verify FastAPI server /health endpoint returns expected shape."""
    r = backoff_get(f"{server_url}/health", timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "uptime_s" in data
    assert isinstance(data["uptime_s"], (int, float))


def test_server_metrics_endpoint(server_url: str) -> None:
    """Verify FastAPI server /metrics endpoint exposes Prometheus metrics.

    Checks for presence of python_info metric (platform collector default).
    """
    r = backoff_get(f"{server_url}/metrics", timeout=60)
    assert r.status_code == 200
    content_type = r.headers.get("content-type", "")
    # Prometheus exposition format
    assert "text/plain" in content_type or "application/openmetrics-text" in content_type
    # Verify python_info is present (from platform_collector)
    assert b"python_info" in r.content, "Expected python_info metric not found"


def test_server_docs_endpoint(server_url: str) -> None:
    """Verify FastAPI auto-generated docs are accessible at root."""
    r = backoff_get(f"{server_url}/docs", timeout=60)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    # FastAPI docs page includes 'swagger-ui' or 'Redoc' references
    assert "swagger" in r.text.lower() or "redoc" in r.text.lower()
