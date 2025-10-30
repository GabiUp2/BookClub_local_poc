"""Tests for Pushgateway metric cleanup behavior.

These tests verify that the PROM_CLEANUP option correctly manages
metric lifecycle in Pushgateway across test runs.

Note: These tests must run sequentially to avoid race conditions
when manipulating shared Pushgateway state.
"""
import os
import subprocess
import time
import urllib.request
import json
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.serial,  # Force sequential execution - all serial tests run on same worker
]

PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")
TEST_JOB = "pytest_cleanup_validation"


def _get_metric_count(job: str) -> int:
    """Query Pushgateway API and count test_duration_seconds metrics for a job."""
    try:
        api_url = f"{PUSHGATEWAY_URL}/api/v1/metrics"
        with urllib.request.urlopen(api_url, timeout=5.0) as response:
            data = json.loads(response.read().decode())
            groups = [g for g in data.get("data", []) if g.get("labels", {}).get("job") == job]
            
            total_metrics = 0
            for group in groups:
                if "test_duration_seconds" in group:
                    total_metrics += len(group["test_duration_seconds"].get("metrics", []))
            return total_metrics
    except Exception as e:
        pytest.fail(f"Failed to query Pushgateway: {e}")


def _delete_all_metrics_for_job(job: str) -> None:
    """Delete all metric groups for a job from Pushgateway."""
    try:
        # Query API to find all metric groups for this job
        api_url = f"{PUSHGATEWAY_URL}/api/v1/metrics"
        with urllib.request.urlopen(api_url, timeout=5.0) as response:
            data = json.loads(response.read().decode())
            groups = [g for g in data.get("data", []) if g.get("labels", {}).get("job") == job]
        
        # Delete each metric group by its full grouping key
        for group in groups:
            labels = group.get("labels", {})
            # Build DELETE URL: /metrics/job/<job>/instance/<instance>/...
            url_parts = [f"{PUSHGATEWAY_URL}/metrics/job/{job}"]
            for key, value in labels.items():
                if key != "job":  # job is already in the path
                    url_parts.append(f"/{key}/{value}")
            delete_url = "".join(url_parts)
            
            req = urllib.request.Request(delete_url, method="DELETE")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                resp.read()
    except Exception:
        pass  # OK if nothing to delete


def _run_pytest_with_cleanup(cleanup_mode: str, test_path: str = "tests/observability/test_monitoring.py::test_server_health_endpoint") -> subprocess.CompletedProcess:
    """Run a single test with specified cleanup mode."""
    cmd = [
        "pytest",
        test_path,
        "-p", "no:xdist",  # Sequential execution for predictable results
        "-o", "addopts=",
        "--pushgw", PUSHGATEWAY_URL,
        "--prom-job", TEST_JOB,
        "--prom-instance", "cleanup_test",
        "--prom-cleanup", cleanup_mode,
        "-q",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)

@pytest.mark.expected_duration("long")
def test_cleanup_none_accumulates_metrics():
    """Verify cleanup=none causes metrics to persist across runs."""
    # Clean slate
    _delete_all_metrics_for_job(TEST_JOB)
    
    time.sleep(0.5)
    initial_count = _get_metric_count(TEST_JOB)
    assert initial_count == 0, f"Expected 0 metrics initially, got {initial_count}"
    
    # Run test twice with cleanup=none
    result1 = _run_pytest_with_cleanup("none")
    assert result1.returncode == 0, f"First test run failed: {result1.stderr}"
    
    time.sleep(0.5)
    count_after_first = _get_metric_count(TEST_JOB)
    assert count_after_first == 1, f"Expected 1 metric after first run, got {count_after_first}"
    
    result2 = _run_pytest_with_cleanup("none")
    assert result2.returncode == 0, f"Second test run failed: {result2.stderr}"
    
    time.sleep(0.5)
    count_after_second = _get_metric_count(TEST_JOB)
    # With cleanup=none, same test with same grouping key overwrites itself (last write wins)
    assert count_after_second == 1, f"Expected 1 metric after second run, got {count_after_second}"
    
    # Clean up
    _delete_all_metrics_for_job(TEST_JOB)

@pytest.mark.expected_duration("long")
def test_cleanup_before_prevents_accumulation():
    """Verify cleanup=before removes old metrics before each run."""
    # Pre-populate with a metric
    _run_pytest_with_cleanup("none")
    time.sleep(0.5)
    
    initial_count = _get_metric_count(TEST_JOB)
    assert initial_count > 0, "Failed to set up initial metrics"
    
    # Run with cleanup=before
    result = _run_pytest_with_cleanup("before")
    assert result.returncode == 0, f"Test run failed: {result.stderr}"
    
    time.sleep(0.5)
    count_after = _get_metric_count(TEST_JOB)
    # Should have only the new run's metrics
    assert count_after == 1, f"Expected 1 metric after cleanup=before, got {count_after}"
    
    # Run again - should still have 1 metric
    result2 = _run_pytest_with_cleanup("before")
    assert result2.returncode == 0, f"Second test run failed: {result2.stderr}"
    
    time.sleep(0.5)
    count_after_second = _get_metric_count(TEST_JOB)
    assert count_after_second == 1, f"Expected 1 metric after second run with cleanup=before, got {count_after_second}"
    
    # Clean up
    _delete_all_metrics_for_job(TEST_JOB)

@pytest.mark.expected_duration("long")
def test_cleanup_after_removes_metrics():
    """Verify cleanup=after removes metrics immediately after push."""
    # Clean slate
    _delete_all_metrics_for_job(TEST_JOB)
    
    time.sleep(0.5)
    initial_count = _get_metric_count(TEST_JOB)
    assert initial_count == 0, f"Expected 0 metrics initially, got {initial_count}"
    
    # Run with cleanup=after
    result = _run_pytest_with_cleanup("after")
    assert result.returncode == 0, f"Test run failed: {result.stderr}"
    
    time.sleep(0.5)
    count_after = _get_metric_count(TEST_JOB)
    # Metrics should be deleted immediately after push
    assert count_after == 0, f"Expected 0 metrics after cleanup=after, got {count_after}"

@pytest.mark.expected_duration("long")
def test_cleanup_both_removes_before_and_after():
    """Verify cleanup=both removes metrics both before and after the run."""
    # Pre-populate
    _run_pytest_with_cleanup("none")
    time.sleep(0.5)
    
    initial_count = _get_metric_count(TEST_JOB)
    assert initial_count > 0, "Failed to set up initial metrics"
    
    # Run with cleanup=both
    result = _run_pytest_with_cleanup("both")
    assert result.returncode == 0, f"Test run failed: {result.stderr}"
    
    time.sleep(0.5)
    count_after = _get_metric_count(TEST_JOB)
    # Should be 0 because cleanup=both deletes after push
    assert count_after == 0, f"Expected 0 metrics after cleanup=both, got {count_after}"


def test_pushgateway_api_accessible():
    """Verify Pushgateway API is accessible."""
    api_url = f"{PUSHGATEWAY_URL}/api/v1/metrics"
    with urllib.request.urlopen(api_url, timeout=5.0) as response:
        data = json.loads(response.read().decode())
        assert "status" in data
        assert data["status"] == "success"


def test_pushgateway_metrics_endpoint_accessible():
    """Verify Pushgateway /metrics endpoint is accessible."""
    metrics_url = f"{PUSHGATEWAY_URL}/metrics"
    with urllib.request.urlopen(metrics_url, timeout=5.0) as response:
        content = response.read().decode()
        # Should contain Pushgateway's own metrics
        assert "pushgateway_build_info" in content or "push_time_seconds" in content
