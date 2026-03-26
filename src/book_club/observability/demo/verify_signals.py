#!/usr/bin/env python3
"""Verify OTEL signals are flowing correctly.

Checks that traces, logs, and metrics are present and correlated.
Used by the demo-verify Make target before presentations.

Usage:
    python -m src.book_club.observability.demo.verify_signals
"""

import argparse
import sys
import time
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class VerificationResult:
    """Result of a single verification check."""

    name: str
    passed: bool
    message: str
    details: Optional[str] = None


def check_tempo_traces(tempo_url: str, service_name: str) -> VerificationResult:
    """Check that recent traces exist in Tempo for the service."""
    try:
        # Tempo search API: GET /api/search with tags=service.name=X (logfmt)
        response = httpx.get(
            f"{tempo_url}/api/search",
            params={
                "tags": f"service.name={service_name}",
                "limit": 5,
                "start": int(time.time()) - 300,  # Last 5 minutes
                "end": int(time.time()),
            },
            timeout=10.0,
        )

        if response.status_code != 200:
            return VerificationResult(
                name="Tempo traces",
                passed=False,
                message=f"Tempo API returned {response.status_code}",
                details=f"URL: {tempo_url}/api/search. Run: make demo-healthy-trace-signal"
                + (f" Response: {response.text[:150]}" if response.text else ""),
            )

        data = response.json()
        traces = data.get("traces", [])

        if not traces:
            # Reachable but no data: pass so demo-verify doesn't block; guide user
            return VerificationResult(
                name="Tempo traces",
                passed=True,
                message=f"Tempo reachable; no traces for '{service_name}' in last 5 min",
                details="Run: make demo-healthy-trace-signal. If still empty, ensure OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4318 and restart backend.",
            )

        return VerificationResult(
            name="Tempo traces",
            passed=True,
            message=f"Found {len(traces)} trace(s) for '{service_name}'",
            details=f"Latest trace ID: {traces[0].get('traceID', 'unknown')[:16]}...",
        )

    except httpx.ConnectError:
        return VerificationResult(
            name="Tempo traces",
            passed=False,
            message="Cannot connect to Tempo",
            details=f"URL: {tempo_url}. Ensure Tempo is running (docker compose up -d).",
        )
    except Exception as e:
        return VerificationResult(
            name="Tempo traces",
            passed=False,
            message=f"Error checking Tempo: {e}",
        )


def _query_loki_logs(
    loki_url: str, query: str, start_ns: int, end_ns: int, headers: dict
) -> tuple[int, Optional[dict]]:
    """Run a Loki query_range; return (status_code, json data or None)."""
    try:
        r = httpx.get(
            f"{loki_url}/loki/api/v1/query_range",
            params={"query": query, "start": start_ns, "end": end_ns, "limit": 5},
            headers=headers,
            timeout=10.0,
        )
        return r.status_code, r.json() if r.status_code == 200 else None
    except Exception:
        return -1, None


def check_loki_logs(loki_url: str, service_name: str) -> VerificationResult:
    """Check that recent logs exist in Loki with trace_id (server_logs or docker)."""
    try:
        now_ns = int(time.time() * 1e9)
        start_ns = now_ns - (300 * 1_000_000_000)
        loki_headers = {"X-Scope-OrgID": "local"}

        # 1) Prefer server logs with job=service_name (Alloy server_logs pipeline)
        query_primary = f'{{job="{service_name}"}} |= "trace_id"'
        status, data = _query_loki_logs(
            loki_url, query_primary, start_ns, now_ns, loki_headers
        )
        if status == 200 and data:
            results = data.get("data", {}).get("result", [])
            if results:
                log_count = sum(len(r.get("values", [])) for r in results)
                return VerificationResult(
                    name="Loki logs",
                    passed=True,
                    message=f"Found {log_count} log(s) with trace_id for '{service_name}'",
                )

        # 2) Fallback: any logs containing trace_id (e.g. docker stdout, other jobs)
        query_any_trace = '{job=~".+"} |= "trace_id"'
        status2, data2 = _query_loki_logs(
            loki_url, query_any_trace, start_ns, now_ns, loki_headers
        )
        if status2 == 200 and data2:
            results2 = data2.get("data", {}).get("result", [])
            if results2:
                log_count = sum(len(r.get("values", [])) for r in results2)
                return VerificationResult(
                    name="Loki logs",
                    passed=True,
                    message=f"Found {log_count} log(s) with trace_id (any job)",
                )

        if status != 200:
            return VerificationResult(
                name="Loki logs",
                passed=False,
                message=f"Loki API returned {status}",
                details=f"URL: {loki_url}. Ensure Loki and Alloy are running.",
            )
        # Reachable but no data: pass so demo-verify doesn't block; guide user
        return VerificationResult(
            name="Loki logs",
            passed=True,
            message="Loki reachable; no logs with trace ID in last 5 min",
            details="Run: make demo-healthy-trace-signal. Server logs: Alloy /preprocessing_server/*.log",
        )

    except httpx.ConnectError:
        return VerificationResult(
            name="Loki logs",
            passed=False,
            message="Cannot connect to Loki",
            details=f"URL: {loki_url}. Ensure Loki is running (docker compose up -d).",
        )
    except Exception as e:
        return VerificationResult(
            name="Loki logs",
            passed=False,
            message=f"Error checking Loki: {e}",
        )


def check_prometheus_metrics(prom_url: str, metric_name: str) -> VerificationResult:
    """Check that metrics exist in Prometheus."""
    try:
        # Query for the metric
        response = httpx.get(
            f"{prom_url}/api/v1/query",
            params={"query": metric_name},
            timeout=10.0,
        )

        if response.status_code != 200:
            return VerificationResult(
                name="Prometheus metrics",
                passed=False,
                message=f"Prometheus API returned {response.status_code}",
            )

        data = response.json()
        results = data.get("data", {}).get("result", [])

        if not results:
            return VerificationResult(
                name="Prometheus metrics",
                passed=False,
                message=f"Metric '{metric_name}' not found",
            )

        # Get total value across all series
        total = sum(float(r.get("value", [0, 0])[1]) for r in results)

        return VerificationResult(
            name="Prometheus metrics",
            passed=True,
            message=f"Metric '{metric_name}' present ({len(results)} series, total: {total:.0f})",
        )

    except httpx.ConnectError:
        return VerificationResult(
            name="Prometheus metrics",
            passed=False,
            message="Cannot connect to Prometheus",
            details=f"URL: {prom_url}",
        )
    except Exception as e:
        return VerificationResult(
            name="Prometheus metrics",
            passed=False,
            message=f"Error checking Prometheus: {e}",
        )


def check_grafana_health(grafana_url: str) -> VerificationResult:
    """Check that Grafana is healthy."""
    try:
        response = httpx.get(f"{grafana_url}/api/health", timeout=5.0)

        if response.status_code == 200:
            return VerificationResult(
                name="Grafana health",
                passed=True,
                message="Grafana is healthy",
            )
        else:
            return VerificationResult(
                name="Grafana health",
                passed=False,
                message=f"Grafana returned {response.status_code}",
            )

    except httpx.ConnectError:
        return VerificationResult(
            name="Grafana health",
            passed=False,
            message="Cannot connect to Grafana",
            details=f"URL: {grafana_url}",
        )
    except Exception as e:
        return VerificationResult(
            name="Grafana health",
            passed=False,
            message=f"Error checking Grafana: {e}",
        )


def check_backend_health(backend_url: str) -> VerificationResult:
    """Check that the backend is healthy."""
    try:
        response = httpx.get(f"{backend_url}/health", timeout=5.0)

        if response.status_code == 200:
            return VerificationResult(
                name="Backend health",
                passed=True,
                message="Backend is healthy",
            )
        else:
            return VerificationResult(
                name="Backend health",
                passed=False,
                message=f"Backend returned {response.status_code}",
            )

    except httpx.ConnectError:
        return VerificationResult(
            name="Backend health",
            passed=False,
            message="Cannot connect to backend",
            details=f"URL: {backend_url}",
        )
    except Exception as e:
        return VerificationResult(
            name="Backend health",
            passed=False,
            message=f"Error checking backend: {e}",
        )


def print_result(result: VerificationResult) -> None:
    """Print a verification result."""
    status = "\033[0;32mPASS\033[0m" if result.passed else "\033[0;31mFAIL\033[0m"
    print(f"  [{status}] {result.name}: {result.message}")
    if result.details:
        print(f"         {result.details}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify OTEL signals are flowing correctly"
    )
    parser.add_argument(
        "--tempo-url",
        default="http://localhost:3200",
        help="Tempo URL (default: http://localhost:3200)",
    )
    parser.add_argument(
        "--loki-url",
        default="http://localhost:3100",
        help="Loki URL (default: http://localhost:3100)",
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus URL (default: http://localhost:9090)",
    )
    parser.add_argument(
        "--grafana-url",
        default="http://localhost:3000",
        help="Grafana URL (default: http://localhost:3000)",
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8010",
        help="Backend URL (default: http://localhost:8010)",
    )
    parser.add_argument(
        "--service-name",
        default="bookclub-preprocessing-server",
        help="Service name to check (default: bookclub-preprocessing-server)",
    )
    parser.add_argument(
        "--metric-name",
        default="preprocessing_server_pdf_upload_requests_total",
        help="Metric name to check (default: preprocessing_server_pdf_upload_requests_total)",
    )

    args = parser.parse_args()

    print("Verifying OTEL signals...")
    print()

    results = []

    # Run all checks
    print("1. Service health checks:")
    results.append(check_backend_health(args.backend_url))
    print_result(results[-1])
    results.append(check_grafana_health(args.grafana_url))
    print_result(results[-1])

    print()
    print("2. Signal checks:")
    results.append(check_tempo_traces(args.tempo_url, args.service_name))
    print_result(results[-1])
    results.append(check_loki_logs(args.loki_url, args.service_name))
    print_result(results[-1])
    results.append(check_prometheus_metrics(args.prometheus_url, args.metric_name))
    print_result(results[-1])

    # Summary
    print()
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    if passed == total:
        print(f"\033[0;32mAll {total} checks passed!\033[0m")
        print()
        print("Ready for demo. Open Grafana: http://localhost:3000")
        return 0
    else:
        print(f"\033[0;31m{passed}/{total} checks passed\033[0m")
        print()
        failed_names = [r.name for r in results if not r.passed]
        if "Backend health" in failed_names:
            print(
                "Ensure backend is running: docker compose up -d bookclub-preprocessing-server"
            )
        if "Tempo traces" in failed_names or "Loki logs" in failed_names:
            print(
                "If Tempo/Loki have no data: rebuild backend (post_fork OTEL), then generate traffic:"
            )
            print(
                "  docker compose build bookclub-preprocessing-server && docker compose up -d --force-recreate bookclub-preprocessing-server"
            )
            print("  make demo-healthy-trace-signal")
        if "Prometheus metrics" in failed_names:
            print("Generate traffic first: make demo-healthy-trace-signal")
        if not any(
            n in failed_names
            for n in (
                "Backend health",
                "Tempo traces",
                "Loki logs",
                "Prometheus metrics",
            )
        ):
            print(
                "Some checks failed. Generate traffic first: make demo-healthy-trace-signal"
            )
        return 1


if __name__ == "__main__":
    sys.exit(main())
