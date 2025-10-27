# Grafana Dashboards

This directory contains pre-configured Grafana dashboards for monitoring test metrics and application execution timings.

## Available Dashboards

### Test Metrics

#### 📊 **Pytest Test Metrics** (`test_metrics_dashboard.json`)
**UID:** `pytest-test-metrics`

Comprehensive dashboard for monitoring pytest test execution metrics pushed to Pushgateway.

**Panels:**
1. **Test Duration by Test Name** - Line chart showing individual test execution times
2. **Slowest Test Duration** - Gauge showing the longest-running test
3. **Total Tests Tracked** - Count of all tests with metrics
4. **Test Duration by File** - Stacked bar chart grouping tests by file
5. **Top 10 Slowest Tests** - Pie chart highlighting bottlenecks
6. **Test Count by Type** - Distribution by test type (unit, integration, etc.)
7. **Test Count by Instance** - pytest-xdist worker distribution
8. **All Tests - Detailed View** - Sortable table with all test details

**Variables:**
- `job` - Filter by pytest job name
- `instance` - Filter by instance/worker

**Use Cases:**
- Identify slow tests that need optimization
- Monitor test suite performance over time
- Track parallel execution across workers
- Verify test metrics pipeline health

---

### Execution Timings

The execution timing dashboards monitor function performance tracked via the `@track_timing` decorator.

#### 🚀 **Execution Timings - Latency & Performance** (`execution_timings_latency.json`)
**UID:** `exec-timings-latency`

Focus on latency percentiles, duration trends, and performance distribution.

**Panels:**
1. **Latency Percentiles (P50, P95, P99)** - Multi-line chart comparing percentiles
2. **Current P95 Latency** - Single stat showing current P95
3. **Current P99 Latency** - Single stat showing current P99
4. **Average Duration** - Mean execution time
5. **Latency Distribution Heatmap** - Visual distribution of response times
6. **Last Execution Duration (Gauge)** - Most recent execution time per function

**Variables:**
- `namespace` - Filter by decorator namespace (server, api, worker, db, etc.)

**Use Cases:**
- Monitor SLA compliance (P95/P99 targets)
- Identify latency spikes or degradation
- Analyze performance distribution patterns
- Track execution time trends

---

#### 📈 **Execution Timings - Throughput & Request Rate** (`execution_timings_throughput.json`)
**UID:** `exec-timings-throughput`

Focus on request rates, call volumes, and throughput patterns.

**Panels:**
1. **Request Rate by Function (req/s)** - Line chart of RPS per function
2. **Total Requests per Second** - Aggregate RPS stat
3. **Total Calls (All Time)** - Cumulative call counter
4. **Request Rate by Status (Stacked)** - Success vs error rates
5. **Call Distribution by Function** - Donut chart showing traffic distribution
6. **Total Calls in Time Range** - Bar chart of calls over time

**Variables:**
- `namespace` - Filter by decorator namespace

**Use Cases:**
- Monitor traffic patterns and load
- Identify most-called functions
- Track throughput over time
- Capacity planning and scaling decisions

---

#### ⚠️ **Execution Timings - Errors & Reliability** (`execution_timings_errors.json`)
**UID:** `exec-timings-errors`

Focus on error rates, failure patterns, and system reliability.

**Panels:**
1. **Overall Success Rate %** - Gauge showing success percentage
2. **Overall Error Rate %** - Gauge showing error percentage
3. **Total Error Count** - Count of all errors
4. **Error Rate % by Function (Over Time)** - Line chart tracking error rates
5. **Total Calls by Function and Status** - Success vs error breakdown
6. **Error Distribution by Function** - Donut chart showing error sources
7. **Error Count (5min buckets)** - Histogram of recent errors

**Variables:**
- `namespace` - Filter by decorator namespace

**Use Cases:**
- Monitor service reliability
- Identify error-prone functions
- Track error rate trends
- Trigger alerts on threshold breaches

---

#### 🎯 **Execution Timings - Overview & SLA** (`execution_timings_overview.json`)
**UID:** `exec-timings-overview`

High-level dashboard combining key metrics for at-a-glance monitoring.

**Panels:**
1. **Global Success Rate %** - Overall system reliability
2. **Global P95 Latency** - System-wide latency target
3. **Global Request Rate** - Total system throughput
4. **Global Error Rate %** - Overall error percentage
5. **Performance Summary by Function** - Table with RPS, P95, Success Rate
6. **P95 Latency Trends by Function** - Historical latency comparison
7. **Request Rate Trends by Function (Stacked)** - Traffic patterns

**Use Cases:**
- Executive/management overview
- SLA monitoring and reporting
- Quick health check
- Cross-function performance comparison
- Starting point for deeper investigation

---

## Importing Dashboards

### Method 1: Via Grafana UI

1. Open Grafana UI: `http://localhost:3000`
2. Navigate to **Dashboards** → **Import**
3. Click **Upload JSON file**
4. Select one of the `.json` files from this directory
5. Configure settings:
   - **Name**: Keep default or customize
   - **Folder**: Choose or create a folder (e.g., "BookClub Metrics")
   - **UID**: Keep default (ensures uniqueness)
   - **Prometheus Data Source**: Select `prometheus`
6. Click **Import**

### Method 2: Via API

```bash
# Set your Grafana API key or admin password
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

# Import dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d @test_metrics_dashboard.json \
  "${GRAFANA_URL}/api/dashboards/db"
```

### Method 3: Provisioning (Docker)

Add to `observability/grafana/provisioning/dashboards/dashboard.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'BookClub Dashboards'
    orgId: 1
    folder: 'BookClub'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: true
```

Mount dashboards in `docker-compose.yml`:

```yaml
services:
  grafana:
    volumes:
      - ./observability/dashboards:/etc/grafana/provisioning/dashboards:ro
```

Restart Grafana to auto-load dashboards.

---

## Dashboard Structure

```
observability/dashboards/
├── README.md                                # This file
├── test_metrics_dashboard.json             # Pytest test metrics
├── execution_timings_latency.json          # Latency & performance
├── execution_timings_throughput.json       # Throughput & request rate
├── execution_timings_errors.json           # Errors & reliability
└── execution_timings_overview.json         # Overview & SLA
```

---

## Data Sources

All dashboards require:

**Prometheus Data Source:**
- **Name:** `prometheus` (default)
- **URL:** `http://prometheus:9090` (or your Prometheus URL)
- **Access:** Server (default)

**Metrics Expected:**

### Test Metrics
- `test_duration_seconds{job, instance, test_name, file, type, expected_duration, tags}`

### Execution Timings
- `{namespace}_{module}_{function}_seconds{status}` - Gauge (last duration)
- `{namespace}_{module}_{function}_calls_total{status}` - Counter (total calls)
- `{namespace}_{module}_{function}_seconds_bucket{status, le}` - Histogram (distribution)

---

## Variables

### Test Metrics Dashboard

| Variable   | Type  | Source                                      | Description              |
|------------|-------|---------------------------------------------|--------------------------|
| `job`      | Query | `label_values(test_duration_seconds, job)` | Pytest job name          |
| `instance` | Query | `label_values(test_duration_seconds, instance)` | Worker instance  |

### Execution Timings Dashboards

| Variable    | Type   | Options                                    | Description              |
|-------------|--------|--------------------------------------------|--------------------------|
| `namespace` | Custom | server, api, worker, db, startup, shutdown | Decorator namespace      |

---

## Customization

### Adjust Thresholds

Edit panel configurations to match your SLA targets:

**Latency thresholds:**
```json
"thresholds": {
  "steps": [
    {"color": "green", "value": null},
    {"color": "yellow", "value": 0.5},  // 500ms
    {"color": "red", "value": 1.0}      // 1 second
  ]
}
```

**Success rate thresholds:**
```json
"thresholds": {
  "steps": [
    {"color": "red", "value": null},
    {"color": "yellow", "value": 95},   // 95%
    {"color": "green", "value": 99}     // 99%
  ]
}
```

### Add Custom Panels

Use existing panels as templates:

1. Click panel title → **Edit**
2. Modify query, visualization type, or settings
3. Save dashboard

### Export Modified Dashboards

1. Dashboard settings (gear icon)
2. **JSON Model**
3. Copy or download JSON
4. Save to this directory
5. Commit to version control

---

## Alerting

### Recommended Alerts

**High Error Rate:**
```yaml
alert: HighErrorRate
expr: |
  sum(rate({__name__=~".*_calls_total", status="error"}[5m]))
  / sum(rate({__name__=~".*_calls_total"}[5m]))
  > 0.05
for: 5m
severity: warning
```

**High P95 Latency:**
```yaml
alert: HighP95Latency
expr: |
  histogram_quantile(0.95,
    sum(rate({__name__=~".*_seconds_bucket", status="ok"}[5m])) by (le)
  ) > 1.0
for: 10m
severity: warning
```

**Slow Test Suite:**
```yaml
alert: SlowTestSuite
expr: |
  max(test_duration_seconds) > 5
for: 1m
severity: info
```

Configure these in `observability/prometheus/alerts.yml`.

---

## Maintenance

### Dashboard Versioning

- Dashboards are versioned in Git
- Changes tracked via commit history
- Use semantic versioning in dashboard title (optional)

### Updates

When updating dashboards:

1. Export updated JSON from Grafana
2. Save to this directory (overwrite existing)
3. Commit with descriptive message
4. Tag release if significant changes

### Testing

Before committing dashboard changes:

1. Test with real data
2. Verify all panels load correctly
3. Check variables work as expected
4. Validate on different time ranges
5. Test on mobile/tablet view (if applicable)

---

## Troubleshooting

### Dashboard Not Loading

**Issue:** "Dashboard not found" error

**Solutions:**
- Check UID is unique
- Verify Prometheus data source exists
- Ensure Grafana has read permissions

### No Data in Panels

**Issue:** Panels show "No data"

**Solutions:**
- Verify metrics exist: `curl http://localhost:9090/api/v1/label/__name__/values`
- Check time range (dashboards default to last 1 hour)
- Verify variable selections (namespace, job, instance)
- Test query in Prometheus UI first

### Variables Not Populating

**Issue:** Variable dropdown empty

**Solutions:**
- Verify query syntax in variable settings
- Check Prometheus data source connection
- Ensure metrics with required labels exist
- Try manual query in Explore view

### Panel Errors

**Issue:** "Query error" or "Timeout"

**Solutions:**
- Simplify query (reduce time range, fewer functions)
- Check Prometheus performance (`up` metric)
- Verify metric cardinality is not too high
- Add query timeout in data source settings

---

## Links

- **Test Metrics Documentation:** `../../docs/test_metrics.md`
- **Test Metrics Verification:** `../../docs/test_metrics_verification.md`
- **Execution Timings Documentation:** `../../docs/execution_timings.md`
- **Execution Timings Verification:** `../../docs/execution_timings_verification.md`
- **Grafana Documentation:** https://grafana.com/docs/
- **Prometheus Query Documentation:** https://prometheus.io/docs/prometheus/latest/querying/basics/

---

## Contributing

To add new dashboards:

1. Create dashboard in Grafana UI
2. Test thoroughly with real data
3. Export JSON (Dashboard settings → JSON Model)
4. Save to this directory with descriptive name
5. Update this README with dashboard description
6. Add to import instructions
7. Commit and create PR

**Naming Convention:**
- Test metrics: `test_*_dashboard.json`
- Execution timings: `execution_timings_*.json`
- Application-specific: `{feature}_dashboard.json`
