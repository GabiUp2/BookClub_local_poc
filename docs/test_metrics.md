# Test Metrics to Prometheus via Pushgateway

## Overview

Test execution times are automatically captured and pushed to Prometheus Pushgateway, making them queryable in Grafana for analysis and monitoring.

## Configuration

Configure via environment variables (`.env`) or CLI flags:

```bash
# .env or .env.example
PUSHGATEWAY_URL=http://localhost:9091
PROM_JOB=pytest
PROM_INSTANCE=dev
PROM_EXTRA_TAGS=branch=main,run_id=local
PROM_CLEANUP=after  # Options: before, after (default), both, none
```

### CLI Flags

- `--pushgw`: Pushgateway URL (default: `http://localhost:9091`)
- `--prom-job`: Job label for grouping (default: `pytest`)
- `--prom-instance`: Instance label (default: hostname)
- `--prom-tags`: Extra comma-separated tags
- `--prom-cleanup`: When to clean old metrics (default: `after`)

### Cleanup Modes

**Default: `cleanup=after`** - Metrics are pushed to Pushgateway, then immediately deleted after Prometheus scrapes them:
- Pushes metrics at end of test session
- Deletes metrics immediately after push
- Prevents metric accumulation
- ⚠️ Prometheus may miss metrics if scrape interval > cleanup time

Other modes:
- `before`: Delete old metrics before new test run (ensures Prometheus gets at least one scrape)
- `both`: Delete before and after (most aggressive cleanup)
- `none`: Never delete (metrics accumulate indefinitely)

### Make Commands

- **`make push-tests`** - Run all tests and push metrics to Pushgateway (uses default cleanup=after)
- **`make verify-test-metrics`** - Verify complete pipeline (pytest → Pushgateway → Prometheus)
- **`make test-cleanup-behavior`** - Test all PROM_CLEANUP options (none, before, after, both)

## Usage

### Via Make

```bash
make push-tests
```

### Via pytest directly

```bash
# Sequential execution
pytest -p no:xdist -o addopts="" --pushgw=http://localhost:9091 \
  --prom-job=pytest --prom-instance=ci --prom-tags=branch=feature,run_id=123

# Parallel execution (default with -n auto)
pytest --pushgw=http://localhost:9091 --prom-job=pytest_ci
```

## Architecture

### Metric Collection Flow

1. **Test execution**: Each test's duration is measured in `pytest_runtest_call` hook
2. **Batch collection**: Metrics collected into session-wide registry (`_session_registry`)
3. **Session end**: All metrics pushed in one batch via `pytest_sessionfinish`
4. **Cleanup**: Old metrics deleted from Pushgateway (if configured with `after` or `both`)

### pytest-xdist Compatibility

With parallel execution (`-n auto`), each worker:
- Maintains its own metric registry
- Pushes with a unique instance label (`dev_gw0`, `dev_gw1`, etc.)
- Prevents workers from overwriting each other's metrics

## Metrics

### Metric Name

`test_duration_seconds` (Gauge)

### Labels

- `test_name`: Full test node ID (sanitised; truncated to 250 chars)
- `file`: Test file path (sanitised; truncated to 200 chars)
- `type`: Test type from `@pytest.mark.test_type("unit")` marker (default: `unspecified`)
- `expected_duration`: From `@pytest.mark.expected_duration("short")` marker (default: `unspecified`)
- `tags`: Extra tags from CLI/env (sanitised; truncated to 120 chars)
- `outcome`: "passed" or "failed"

Added by prometheus
- `instance`: Instance identifier (includes worker ID for parallel runs)
- `job`: Prometheus scarping job name as a label for grouping by source

### Example Markers

```python
import pytest

@pytest.mark.test_type("integration")
@pytest.mark.expected_duration("long")
def test_slow_operation():
    ...
```

Register custom markers in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "test_type(name): categorise tests by type (unit, integration, e2e)",
    "expected_duration(name): expected runtime bucket (short, medium, long)",
]
```

## Grafana Dashboards

### Pre-built Dashboard

**📊 Pytest Test Metrics Dashboard**
- **Location:** `observability/dashboards/test_metrics_dashboard.json`
- **Import:** See `observability/dashboards/README.md` for instructions

**Panels included:**
1. Test Duration by Test Name - Individual test performance
2. Slowest Test Duration - Identify bottlenecks
3. Total Tests Tracked - Coverage validation
4. Test Duration by File - File-level aggregation
5. Top 10 Slowest Tests - Quick bottleneck identification
6. Test Count by Type - Distribution by test type
7. Test Count by Instance - pytest-xdist worker distribution
8. All Tests - Detailed View - Sortable table with all metrics

**Variables:**
- `job` - Filter by pytest job name
- `instance` - Filter by instance/worker

### Quick Import

```bash
# Via Grafana UI
# 1. Navigate to Dashboards → Import
# 2. Upload: observability/dashboards/test_metrics_dashboard.json
# 3. Select Prometheus data source
# 4. Click Import

# Via API
curl -X POST \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d @observability/dashboards/test_metrics_dashboard.json \
  http://localhost:3000/api/dashboards/db
```

## Grafana Queries

### Basic Queries

```promql
# All test durations
test_duration_seconds

# Average duration by file
avg by (file) (test_duration_seconds)

# Top 10 slowest tests
topk(10, test_duration_seconds)

# Tests from specific worker
test_duration_seconds{instance=~"dev_gw.*"}

# Filter by tags
test_duration_seconds{tags=~".*branch_main.*"}
```

### Dashboard Examples

**Slowest Tests Table**
- Query: `sort_desc(test_duration_seconds{job="pytest"})`
- Visualization: Table
- Transform: Group by `test_name`

**Test Duration Heatmap**
- Query: `test_duration_seconds`
- Visualization: Heatmap
- Group by: `file`, `type`

**Duration Over Time**
- Query: `test_duration_seconds{file="tests_integration_test_metrics.py"}`
- Visualization: Time series
- Use Prometheus range queries to see trends

## Troubleshooting

### Metrics not appearing in Prometheus

1. **Check Pushgateway**:
   ```bash
   curl http://localhost:9091/metrics | grep test_duration_seconds
   ```

2. **Check Prometheus targets**:
   ```bash
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="pushgateway")'
   ```

3. **Check Prometheus scrape config**:
   ```yaml
   scrape_configs:
     - job_name: 'pushgateway'
       static_configs:
         - targets: ['pushgateway:9091']
   ```

4. **Run verification**:
   ```bash
   make verify-test-metrics
   ```

### Metrics accumulating

Pushgateway persists metrics until explicitly deleted. To clean up:

```bash
# Delete all metrics for a specific job
curl -X DELETE http://localhost:9091/metrics/job/pytest

# Or use the test cleanup utilities
make test-cleanup-behavior
```

### Cardinality concerns

Labels are automatically truncated to limit cardinality:
- `test_name`: 250 chars
- `file`: 200 chars
- `tags`: 120 chars

For large test suites, consider:
- Grouping by file instead of test_name in Grafana
- Using fewer unique tag values
- Aggregating metrics at ingestion time

## Implementation Details

See `tests/conftest.py`:
- `pytest_sessionstart`: Cleanup old metrics (if `cleanup=before` or `cleanup=both`)
- `pytest_runtest_call`: Measure and collect test duration
- `pytest_sessionfinish`: Push all metrics in batch + cleanup (if `cleanup=after` or `cleanup=both`)
- `_cleanup_pushgateway`: Query API and delete all instances for the job
- `_collect_test_metric`: Add test metric to session-wide registry
- `_get_marker_arg`: Extract custom marker values (test_type, expected_duration)
- `_norm`: Sanitize label values for Prometheus compatibility

## References

- [Prometheus Pushgateway](https://github.com/prometheus/pushgateway)
- [prometheus_client Python library](https://github.com/prometheus/client_python)
- [pytest hooks documentation](https://docs.pytest.org/en/stable/reference/reference.html#hooks)
