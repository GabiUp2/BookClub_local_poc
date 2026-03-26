# Test Metrics Verification

## Overview

Comprehensive verification and testing of the test metrics pipeline (pytest → Pushgateway → Prometheus → Grafana).

## Make Targets

### `make verify-test-metrics`

Complete end-to-end verification of the test metrics pipeline.

**Steps:**
1. Run a single test with metrics push
2. Verify metrics appear in Pushgateway
3. Check Prometheus is scraping Pushgateway (target status)
4. Verify metrics reached Prometheus (may need to wait for scrape interval)
5. Test cleanup behavior
6. Clean up verification metrics

**Usage:**
```bash
make verify-test-metrics
```

**Output Example:**
```
Verifying test metrics pipeline...

1. Running tests with metrics push...
Test executed successfully

2️. Checking metrics in Pushgateway...
Found 1 metric(s) in Pushgateway
test_duration_seconds{...} 0.006385104003129527

3️. Checking Prometheus scrape target for Pushgateway...
Prometheus is scraping Pushgateway (status: up)

4️. Verifying metrics reached Prometheus...
Metrics not yet in Prometheus (may need to wait for scrape interval)

5️. Testing cleanup behavior...
.                                                                        [100%]

6️. Cleaning up verification metrics...
Cleanup complete

Test metrics pipeline verification complete!
   Pushgateway: http://localhost:9091
   Prometheus:  http://localhost:9090
   Grafana:     http://localhost:3000
```

### `make test-cleanup-behavior`

Test all `PROM_CLEANUP` options (none, before, after, both) to verify correct behavior.

**Tests executed:**
- `test_cleanup_none_accumulates_metrics` - Verify cleanup=none preserves metrics
- `test_cleanup_before_prevents_accumulation` - Verify cleanup=before removes old metrics
- `test_cleanup_after_removes_metrics` - Verify cleanup=after removes metrics immediately
- `test_cleanup_both_removes_before_and_after` - Verify cleanup=both cleans before and after
- `test_pushgateway_api_accessible` - Verify Pushgateway API is accessible
- `test_pushgateway_metrics_endpoint_accessible` - Verify Pushgateway /metrics endpoint

**Usage:**
```bash
make test-cleanup-behavior
```

**Output Example:**
```
Testing Pushgateway cleanup behavior...
   (Running sequentially to avoid race conditions)
============================= test session starts ==============================
...
tests/observability/test_pushgateway_cleanup.py::test_cleanup_none_accumulates_metrics PASSED [ 16%]
tests/observability/test_pushgateway_cleanup.py::test_cleanup_before_prevents_accumulation PASSED [ 33%]
tests/observability/test_pushgateway_cleanup.py::test_cleanup_after_removes_metrics PASSED [ 50%]
tests/observability/test_pushgateway_cleanup.py::test_cleanup_both_removes_before_and_after PASSED [ 66%]
tests/observability/test_pushgateway_cleanup.py::test_pushgateway_api_accessible PASSED [ 83%]
tests/observability/test_pushgateway_cleanup.py::test_pushgateway_metrics_endpoint_accessible PASSED [100%]

============================== 6 passed in 26.42s ==============================
```

### `make push-tests`

Run all tests and push metrics to Pushgateway (standard test run with metrics).

**Usage:**
```bash
make push-tests
```

## Test File

Location: `tests/observability/test_pushgateway_cleanup.py`

### Key Features

1. **Sequential execution** - Tests run sequentially to avoid race conditions when manipulating shared Pushgateway state
2. **Comprehensive cleanup** - Uses the same cleanup logic as conftest.py to properly delete all metric groups
3. **Cleanup mode validation** - Tests verify each cleanup mode behaves correctly:
   - `none`: Metrics persist across runs
   - `before`: Old metrics deleted before each run
   - `after`: Metrics deleted immediately after push (default)
   - `both`: Cleanup before and after

### Helper Functions

- `_get_metric_count(job)` - Query Pushgateway API and count metrics for a job
- `_delete_all_metrics_for_job(job)` - Comprehensively delete all metric groups for a job
- `_run_pytest_with_cleanup(mode)` - Run a test with specified cleanup mode

## Integration with CI/CD

### Pre-deployment Verification

```bash
# Verify complete pipeline before deployment
make verify-test-metrics

# Run cleanup behavior tests to ensure proper metric lifecycle
make test-cleanup-behavior
```

### Continuous Testing

For continuous test runs every 5-10 minutes:

```bash
# Use cleanup=after (default) to clean after each run
make push-tests

# Or use cleanup=before to ensure Prometheus gets at least one scrape
export PROM_CLEANUP=before
make push-tests
```

## Troubleshooting

### Metrics not in Pushgateway

**Check test execution:**
```bash
# Run a single test and verify it pushed metrics
pytest tests/observability/test_monitoring.py::test_server_health_endpoint \
  -p no:xdist -o addopts="" \
  --pushgw=http://localhost:9091 \
  --prom-job=test_debug \
  -v
```

**Check Pushgateway directly:**
```bash
curl http://localhost:9091/metrics | grep test_duration_seconds
```

### Metrics not in Prometheus

**Check Prometheus target:**
```bash
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="pushgateway")'
```

**Wait for scrape interval:**
Prometheus scrapes Pushgateway at a configured interval (default 15s-1m). Metrics may take time to appear.

### Cleanup tests failing

**Ensure sequential execution:**
The cleanup tests must run sequentially to avoid race conditions. The Makefile target already handles this with `-p no:xdist -o addopts=""`.

**Manual cleanup:**
```bash
# Clean all test metrics
curl -X DELETE http://localhost:9091/metrics/job/pytest_cleanup_validation
```

## Configuration

All configuration options are documented in `docs/test_metrics.md`.

### Environment Variables

- `PUSHGATEWAY_URL` - Pushgateway URL (default: `http://localhost:9091`)
- `PROM_JOB` - Job label (default: `pytest`)
- `PROM_INSTANCE` - Instance label (default: hostname)
- `PROM_EXTRA_TAGS` - Extra tags (comma-separated)
- `PROM_CLEANUP` - Cleanup mode: `before`, `after` (default), `both`, `none`

## Architecture

```
pytest tests/
    (measure duration)
conftest.py::pytest_runtest_call
    (collect metrics)
_session_registry (batch)
    (push at session end)
Pushgateway
    (scrape)
Prometheus
    (query)
Grafana
```

### Key Components

1. **conftest.py** - Hooks into pytest lifecycle to measure and push metrics in batch at session end
2. **Pushgateway** - Ephemeral metric buffer for batch-style pushes (auto-cleanup with `after` mode)
3. **Prometheus** - Time-series database that scrapes Pushgateway
4. **Grafana** - Visualization and dashboarding

## See Also

- [Test Metrics Documentation](./test_metrics.md) - Complete guide to test metrics
- [Pushgateway Documentation](https://github.com/prometheus/pushgateway)
- [pytest Hooks Reference](https://docs.pytest.org/en/stable/reference/reference.html#hooks)
