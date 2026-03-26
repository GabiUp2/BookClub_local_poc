"""
Integration test: frontend OTLP trace path (app proxy -> Alloy -> Tempo).

POSTs a minimal OTLP/HTTP JSON trace with service name bookclub-app to the
Next.js proxy, then queries Tempo to confirm the trace was ingested.
Requires: app on APP_BASE (default localhost:8000), Tempo on 3200.
"""

import os
import time

import pytest
import requests

pytestmark = pytest.mark.integration

APP_BASE = os.getenv("APP_BASE", "http://localhost:8000")
TEMPO_BASE = os.getenv("TEMPO_BASE", "http://localhost:3200")
# Allow Tempo ingestion delay (Alloy -> Tempo can take a few seconds)
TEMPO_POLL_WAIT_S = 2
TEMPO_POLL_ATTEMPTS = 4


def _minimal_otlp_trace():
    """Minimal OTLP JSON ExportTraceServiceRequest with current-time span."""
    now_ns = int(time.time() * 1e9)
    return {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "bookclub-app"}},
                    ],
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "integration-test"},
                        "spans": [
                            {
                                "traceId": "5b8efff798038103d269b633813fc60c",
                                "spanId": "eee19b7ec3c1b174",
                                "name": "test-span",
                                "kind": 1,
                                "startTimeUnixNano": str(now_ns),
                                "endTimeUnixNano": str(now_ns + 1_000_000_000),
                            },
                        ],
                    },
                ],
            },
        ],
    }


@pytest.mark.expected_duration("medium")
def test_frontend_otel_proxy_forwards_to_tempo():
    """POST OTLP trace via app proxy; verify Tempo receives it (bookclub-app service)."""
    # 1. Send trace through Next.js proxy (skip if app not ready, e.g. fresh containers)
    url = f"{APP_BASE}/api/otel/v1/traces"
    try:
        resp = requests.post(
            url,
            json=_minimal_otlp_trace(),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
    except requests.RequestException as e:
        pytest.skip(
            f"App proxy unreachable at {url}: {e}. "
            "Start stack: docker compose up -d; wait for bookclub-app to be ready."
        )
    if resp.status_code != 200:
        pytest.skip(
            f"App proxy returned {resp.status_code} at {url}. "
            "Ensure bookclub-app is running and ALLOY_OTLP_ENDPOINT is set."
        )

    # 2. Poll Tempo until bookclub-app appears or max attempts (Alloy -> Tempo can be delayed)
    search_url = f"{TEMPO_BASE}/api/search"
    service_names = set()
    for _ in range(TEMPO_POLL_ATTEMPTS):
        time.sleep(TEMPO_POLL_WAIT_S)
        try:
            r = requests.get(search_url, params={"limit": 50}, timeout=10)
            if r.ok:
                data = r.json()
                traces = data.get("traces") or []
                service_names = {t.get("rootServiceName") for t in traces if t.get("rootServiceName")}
                if "bookclub-app" in service_names:
                    return
        except requests.RequestException:
            pass

    assert "bookclub-app" in service_names, (
        f"Expected bookclub-app in Tempo after {TEMPO_POLL_ATTEMPTS} attempts; got services: {service_names}. "
        "Ensure Alloy and Tempo are running; proxy forwards to http://alloy:4318."
    )
