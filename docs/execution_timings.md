# Execution Timings - Function Performance Tracking

## Overview

`ExecutionTimings.py` provides a decorator-based system for tracking function execution time and call statistics using Prometheus metrics. It automatically measures function performance and exposes metrics for monitoring in Grafana.

**Key Features:**
- 🎯 **Simple decorator** - `@track_timing()` on any function
- ⚡ **Async/sync support** - Works with both synchronous and asynchronous functions
- 📊 **Three metric types** - Gauge (last duration), Counter (total calls), Histogram (distribution)
- 🔄 **Gunicorn compatible** - Supports multiprocess mode with worker aggregation
- 🔗 **Trace integration** - Exemplar support for linking to Tempo traces
- 🎨 **Automatic naming** - Metrics named from module path and function name
- ⚠️ **Error tracking** - Separate metrics for successful and failed executions

## Configuration

### Environment Variables

No explicit configuration required. The decorator uses the default Prometheus registry and is compatible with:

```bash
# Single-process mode (development)
# No additional configuration needed

# Multiprocess mode (Gunicorn production)
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
```

### Registry

By default, uses `prometheus_client.REGISTRY` (the global default registry). This ensures metrics are automatically included in the `/metrics` endpoint.

## Usage

### Basic Decorator Usage

```python
from book_club.observability.ExecutionTimings import track_timing

# Synchronous function
@track_timing(namespace="server")
def process_data(data: dict) -> dict:
    # Your logic here
    return {"status": "processed"}

# Asynchronous function
@track_timing(namespace="server")
async def fetch_user(user_id: int) -> dict:
    # Your async logic here
    return {"id": user_id, "name": "Alice"}
```

### Namespace Customization

The `namespace` parameter prefixes all metric names for logical grouping:

```python
# Startup/shutdown events
@track_timing(namespace="startup")
async def startup():
    # Initialization logic
    pass

# API endpoints
@track_timing(namespace="api")
async def health() -> dict:
    return {"status": "ok"}

# Background workers
@track_timing(namespace="worker")
def process_queue_item(item):
    # Processing logic
    pass

# Database operations
@track_timing(namespace="db")
async def fetch_records(query: str):
    # Database query
    pass
```

### Error Handling

The decorator automatically tracks errors with `status="error"` label:

```python
@track_timing(namespace="server")
def risky_operation(value: int) -> int:
    if value < 0:
        raise ValueError("Negative value not allowed")
    return value * 2

# Metrics will show:
# - status="ok" for successful calls
# - status="error" for failed calls
```

### Trace Integration (Exemplars)

Link metrics to distributed traces by passing `_trace_id` as a keyword argument:

```python
@track_timing(namespace="api")
async def handle_request(request_data: dict, _trace_id: str = None):
    # Process request
    return {"result": "success"}

# Call with trace ID
result = await handle_request(data, _trace_id="trace-abc-123-xyz")
```

**Note:** Exemplars require:
- Prometheus with exemplar support enabled
- Tempo or another tracing backend configured
- Modern `prometheus_client` library (v0.13.0+)

### Custom Histogram Buckets

For fine-grained latency percentiles:

```python
from book_club.observability.ExecutionTimings import track_timing

# Adjust buckets for microsecond-level operations
@track_timing(
    namespace="cache",
    histogram_buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05)
)
def get_from_cache(key: str):
    # Fast cache lookup
    return cache[key]
```

**Default buckets:** `(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5)` seconds

## Architecture

### Decorator Flow

```
Function Call
    ↓
@track_timing wrapper
    ↓
Start timer (perf_counter)
    ↓
Execute function (sync/async)
    ↓ (success/error)
Stop timer
    ↓
Update metrics:
    - Gauge.set(duration)
    - Counter.inc()
    - Histogram.observe(duration, exemplar?)
    ↓
Return result / Re-raise exception
```

### Metric Lifecycle

```
Decorator Applied (import time)
    ↓
Metrics lazy-initialized on first call
    ↓
    ├─ Gauge created
    ├─ Counter created
    └─ Histogram created
    ↓
Metrics registered in DEFAULT_REGISTRY
    ↓
Available at /metrics endpoint
    ↓
Prometheus scrapes /metrics
    ↓
Grafana queries Prometheus
```

### Multiprocess Mode (Gunicorn)

```
Gunicorn Master Process
    ↓
Fork Workers (4x)
    ↓
Each Worker:
    - Inherits DEFAULT_REGISTRY
    - Writes metrics to PROMETHEUS_MULTIPROC_DIR/*.db files
    - Uses NoOpMetric for duplicate registrations
    ↓
/metrics endpoint aggregates all worker files
    ↓
Single unified view in Prometheus
```

## Metrics Exposed

For a function decorated with `@track_timing(namespace="server")`, three metrics are created:

### 1. Gauge - Last Execution Duration

**Metric Name:** `{namespace}_{module}_{function}_seconds`

**Example:** `server_book_club_server_server_main_startup_seconds`

**Labels:**
- `status` - "ok" or "error"

**Purpose:** Track the most recent execution time

**Grafana Query:**
```promql
server_book_club_server_server_main_startup_seconds{status="ok"}
```

### 2. Counter - Total Calls

**Metric Name:** `{namespace}_{module}_{function}_calls_total`

**Example:** `server_book_club_server_server_main_startup_calls_total`

**Labels:**
- `status` - "ok" or "error"

**Purpose:** Count successful and failed invocations

**Grafana Query:**
```promql
# Total calls
sum(server_book_club_server_server_main_startup_calls_total)

# Success rate
rate(server_book_club_server_server_main_startup_calls_total{status="ok"}[5m])
/ rate(server_book_club_server_server_main_startup_calls_total[5m])
```

### 3. Histogram - Duration Distribution

**Metric Name:** `{namespace}_{module}_{function}_seconds` (with `_bucket`, `_sum`, `_count` suffixes)

**Example:** `server_book_club_server_server_main_startup_seconds_bucket`

**Labels:**
- `status` - "ok" or "error"
- `le` - Less-than-or-equal bucket bound (automatically added by Prometheus)

**Purpose:** Calculate percentiles (p50, p95, p99) and distributions

**Grafana Query:**
```promql
# P95 latency
histogram_quantile(0.95, 
  rate(server_book_club_server_server_main_startup_seconds_bucket{status="ok"}[5m])
)

# P99 latency
histogram_quantile(0.99, 
  rate(server_book_club_server_server_main_startup_seconds_bucket{status="ok"}[5m])
)

# Average duration
rate(server_book_club_server_server_main_startup_seconds_sum{status="ok"}[5m])
/ rate(server_book_club_server_server_main_startup_seconds_count{status="ok"}[5m])
```

## Real-World Example

### Server Startup Tracking

```python
# src/book_club/server/server_main.py

from observability.ExecutionTimings import track_timing

@server.on_event("startup")
@track_timing(namespace="startup")
async def startup():
    server.state.started_at = time.time()
    server.state.app_env = os.getenv("APP_ENV", "local")
    logger.info("Server started")
```

**Metrics Generated:**
- `startup_book_club_server_server_main_startup_seconds{status="ok"}` - Last startup duration
- `startup_book_club_server_server_main_startup_calls_total{status="ok"}` - Number of startups
- `startup_book_club_server_server_main_startup_seconds_bucket` - Startup time distribution

### API Endpoint Tracking

```python
@server.get("/ingest")
@track_timing(namespace="api")
async def ingest(data: dict) -> dict:
    # Process ingestion
    return {"status": "ingested", "count": len(data)}
```

**Metrics Generated:**
- `api_book_club_server_server_main_ingest_seconds{status="ok"}`
- `api_book_club_server_server_main_ingest_calls_total{status="ok"}`
- `api_book_club_server_server_main_ingest_seconds_bucket`

### Error Rate Monitoring

```python
@track_timing(namespace="api")
async def generate_flashcards(text: str, _trace_id: str = None):
    if not text:
        raise ValueError("Text cannot be empty")
    # Generate flashcards
    return {"cards": [...]}

# Successful call: status="ok"
# Failed call: status="error"
```

**Error Rate Query:**
```promql
sum(rate(api_book_club_server_server_main_generate_flashcards_calls_total{status="error"}[5m]))
/ sum(rate(api_book_club_server_server_main_generate_flashcards_calls_total[5m]))
```

## Multiprocess Mode (Gunicorn)

### Setup

1. **Set environment variable:**
```bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p $PROMETHEUS_MULTIPROC_DIR
```

2. **Use multiprocess collector in /metrics endpoint:**
```python
from prometheus_client import CollectorRegistry, multiprocess, generate_latest

@server.get("/metrics")
async def metrics():
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        # Multiprocess mode: aggregate from all workers
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
    else:
        # Single-process mode
        data = generate_latest(REGISTRY)
    return Response(data, media_type=CONTENT_TYPE_LATEST)
```

3. **Run with Gunicorn:**
```bash
gunicorn -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8010 \
  book_club.server.server_main:server
```

### How It Works

- Each Gunicorn worker writes metrics to separate `.db` files in `PROMETHEUS_MULTIPROC_DIR`
- The `/metrics` endpoint aggregates all worker files using `MultiProcessCollector`
- Metrics are summed across workers (Counters, Histograms) or use max (Gauges)
- **NoOpMetric fallback** - If a worker tries to re-register a metric, it uses a no-op placeholder (actual metrics still work via file writes)

### Worker Cleanup

**Important:** Clean up multiprocess files when starting fresh:

```bash
# Clear old metrics before starting
rm -rf /tmp/prometheus_multiproc/*

# Or in Docker entrypoint
rm -f ${PROMETHEUS_MULTIPROC_DIR}/*.db
```

## Troubleshooting

### Metrics Not Appearing

**1. Check decorator is applied:**
```python
@track_timing(namespace="server")  # Must be present
def my_function():
    pass
```

**2. Ensure function is called at least once:**
Metrics are lazy-initialized on first invocation.

**3. Verify /metrics endpoint:**
```bash
curl http://localhost:8010/metrics | grep "server_.*_seconds"
```

### Duplicate Registration Errors

**Symptom:**
```
ValueError: Duplicated timeseries in CollectorRegistry
```

**Cause:** Metric already registered (common in Gunicorn multiprocess mode)

**Solution:** Already handled by `_NoOpMetric` fallback. Metrics still work via file writes.

### Metrics Reset to Zero

**Multiprocess mode issue:**
- Gauges show max value across workers
- Counters/Histograms aggregate correctly
- If only one worker is active, only that worker's metrics appear

**Single-process issue:**
- Metrics persist in memory until restart
- Restart clears all metrics

### Exemplars Not Showing

**Requirements:**
1. **Prometheus:** Enable exemplars in `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  scrape_timeout: 10s
  evaluation_interval: 15s
  external_labels:
    cluster: local
  # Enable exemplar storage
  exemplars:
    max_exemplars: 100000
```

2. **prometheus_client:** Version >= 0.13.0
```bash
pip install 'prometheus-client>=0.13.0'
```

3. **Pass _trace_id:**
```python
await my_function(data, _trace_id="trace-123-abc")
```

4. **Link to Tempo in Grafana:**
Configure Tempo as data source with trace ID field mapping.

### Slow Performance

**High cardinality warning:**
- Labels create unique time series
- `status` label is low-cardinality (only "ok" and "error")
- **Never** add request IDs, user IDs, or other high-cardinality values as labels
- Use exemplars for trace IDs instead

**Histogram bucket tuning:**
- Default buckets cover 1ms to 5s
- Adjust for your latency profile:
  - **Fast operations (<10ms):** `(0.001, 0.005, 0.01, 0.05)`
  - **Slow operations (>1s):** `(0.5, 1, 2, 5, 10, 30)`

## Implementation Details

### Key Components

**File:** `src/book_club/observability/ExecutionTimings.py`

**Functions:**
- `track_timing(namespace, registry)` - Main decorator factory
- `_get_or_create(fn, namespace, histogram_buckets)` - Lazy metric creation with caching
- `_metric_names(fn, namespace)` - Generate metric names from function metadata
- `metrics_text()` - Export metrics as bytes (for debugging)
- `metrics_content_type()` - Return Prometheus content type

**Classes:**
- `_NoOpMetric` - Placeholder for multiprocess duplicate registration fallback

**Module-Level Caches:**
- `_GAUGES` - Gauge metric cache (dict)
- `_COUNTERS` - Counter metric cache (dict)
- `_HISTOS` - Histogram metric cache (dict)

### Metric Naming Convention

```
{namespace}_{module_path}_{function_name}_{metric_type}
```

**Example:**
```python
# Module: book_club.server.routes
# Function: get_health
# Namespace: api

# Results in:
api_book_club_server_routes_get_health_seconds  # Gauge
api_book_club_server_routes_get_health_calls_total  # Counter
api_book_club_server_routes_get_health_seconds_bucket  # Histogram
```

**Module path transformation:**
- Dots replaced with underscores: `book.club.server` → `book_club_server`

### Lazy Initialization

Metrics are **not** created at decoration time (import). They are created on **first function call**:

```python
@track_timing(namespace="server")  # No metrics created yet
def my_function():
    pass

my_function()  # NOW metrics are created and registered
```

**Reason:** Avoids Gunicorn multiprocess issues where decorators run in master process before fork.

## Testing

### Unit Tests

Location: `tests/observability/test_executiontimings.py`

**Coverage:**
- ✅ Sync function tracking
- ✅ Async function tracking
- ✅ Error tracking (status="error")
- ✅ Duration recording
- ✅ Counter increments
- ✅ Trace ID exemplars
- ✅ Metric caching
- ✅ Multiprocess duplicate registration fallback
- ✅ Custom histogram buckets
- ✅ Function metadata preservation

**Run tests:**
```bash
# All execution timing tests
make test-executiontimings  # If target exists

# Or directly with pytest
pytest tests/observability/test_executiontimings.py -v

# Specific test
pytest tests/observability/test_executiontimings.py::test_track_timing_sync_function_success -v
```

### Integration Testing

**Check metrics endpoint:**
```bash
# Start server
make dev

# Generate some traffic
curl http://localhost:8010/health
curl http://localhost:8010/ingest

# Check metrics
curl http://localhost:8010/metrics | grep "server_.*_seconds"
```

**Expected output:**
```
server_book_club_server_server_main_startup_seconds{status="ok"} 0.0123
server_book_club_server_server_main_startup_calls_total{status="ok"} 1.0
server_book_club_server_server_main_startup_seconds_bucket{le="0.005",status="ok"} 0.0
...
```

## Grafana Dashboards

### Pre-built Dashboards

Four focused dashboards for comprehensive execution timing monitoring:

#### 🚀 **Latency & Performance** (`execution_timings_latency.json`)
**Focus:** Response times, percentiles, distribution

**Panels:**
- P50/P95/P99 Latency Percentiles
- Current P95/P99 Latency Stats
- Average Duration
- Latency Distribution Heatmap
- Last Execution Duration (Gauge)

#### 📈 **Throughput & Request Rate** (`execution_timings_throughput.json`)
**Focus:** Traffic patterns, call volumes

**Panels:**
- Request Rate by Function
- Total Requests per Second
- Total Calls (All Time)
- Request Rate by Status (Stacked)
- Call Distribution by Function
- Total Calls in Time Range

#### ⚠️ **Errors & Reliability** (`execution_timings_errors.json`)
**Focus:** Failures, success rates, reliability

**Panels:**
- Overall Success Rate %
- Overall Error Rate %
- Total Error Count
- Error Rate % by Function (Over Time)
- Total Calls by Function and Status
- Error Distribution by Function
- Error Count (5min buckets)

#### 🎯 **Overview & SLA** (`execution_timings_overview.json`)
**Focus:** High-level metrics, SLA monitoring

**Panels:**
- Global Success Rate %
- Global P95 Latency
- Global Request Rate
- Global Error Rate %
- Performance Summary by Function (Table)
- P95 Latency Trends
- Request Rate Trends (Stacked)

### Quick Import

```bash
# Import all dashboards
cd observability/dashboards
for dash in execution_timings_*.json; do
  curl -X POST \
    -H "Content-Type: application/json" \
    -u "admin:admin" \
    -d @"$dash" \
    http://localhost:3000/api/dashboards/db
done
```

**Or via Grafana UI:**
1. Navigate to **Dashboards** → **Import**
2. Upload JSON files from `observability/dashboards/`
3. Select **Prometheus** data source
4. Click **Import**

**See:** `observability/dashboards/README.md` for detailed instructions

## Best Practices

### DO ✅

- Use descriptive namespaces (`api`, `worker`, `db`, `cache`)
- Track critical paths (API endpoints, database queries, external calls)
- Keep function names descriptive (metrics inherit the name)
- Use `status` label for success/error tracking
- Pass `_trace_id` for distributed tracing integration
- Adjust histogram buckets to match expected latency
- Set up alerts on P95/P99 latency and error rate

### DON'T ❌

- Don't add high-cardinality labels (user IDs, request IDs)
- Don't decorate every tiny function (overhead adds up)
- Don't ignore multiprocess setup for Gunicorn production
- Don't forget to clean multiprocess dir on restart
- Don't use this for CPU profiling (use py-spy or cProfile instead)
- Don't track functions that execute millions of times per second (overhead)

## Future Enhancements

- [ ] Automatic Tempo trace linking via OpenTelemetry context
- [ ] Configurable alert thresholds per function
- [ ] Memory usage tracking alongside execution time
- [ ] Custom labels via decorator parameters
- [ ] Automatic SLO tracking (latency < Xms, success rate > Y%)

## References

- [Prometheus Client Python](https://github.com/prometheus/client_python)
- [Prometheus Histogram Best Practices](https://prometheus.io/docs/practices/histograms/)
- [Prometheus Exemplars](https://prometheus.io/docs/prometheus/latest/feature_flags/#exemplars-storage)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [Gunicorn Multiprocess Mode](https://github.com/prometheus/client_python#multiprocess-mode-eg-gunicorn)
