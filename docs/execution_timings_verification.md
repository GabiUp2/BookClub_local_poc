# Execution Timings Verification & Integration Guide

## Overview

Practical guide for verifying, testing, and integrating the execution timing metrics system into your application.

## Quick Verification

### 1. Start the Server

```bash
# Development mode (single process)
make dev

# Or manually
uvicorn book_club.server.server_main:server --host 0.0.0.0 --port 8010 --reload
```

### 2. Generate Traffic

```bash
# Hit instrumented endpoints
curl http://localhost:8010/health
curl http://localhost:8010/ingest
curl http://localhost:8010/generate_flashcards
```

### 3. Check Metrics

```bash
# View all metrics
curl http://localhost:8010/metrics

# Filter for execution timing metrics
curl http://localhost:8010/metrics | grep "_seconds{" | grep "server_book_club"

# Check specific function
curl http://localhost:8010/metrics | grep "startup_book_club_server_server_main_startup"
```

### 4. Verify in Prometheus

```bash
# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=server_book_club_server_server_main_startup_seconds'

# Or open Prometheus UI
open http://localhost:9090
```

### 5. Visualize in Grafana

```bash
# Open Grafana
open http://localhost:3000

# Import or create dashboard with panels
```

## Integration Steps

### Step 1: Import the Decorator

```python
from book_club.observability.ExecutionTimings import track_timing
```

### Step 2: Decorate Your Functions

**Synchronous function:**
```python
@track_timing(namespace="api")
def process_document(doc: dict) -> dict:
    # Your logic
    return {"status": "processed"}
```

**Asynchronous function:**
```python
@track_timing(namespace="api")
async def fetch_embeddings(text: str) -> list:
    # Your async logic
    return embeddings
```

**With trace integration:**
```python
@track_timing(namespace="api")
async def generate_flashcards(text: str, _trace_id: str = None):
    # Process with optional trace ID
    return {"cards": [...]}
```

### Step 3: Configure Multiprocess Mode (Production)

**Docker Compose:**
```yaml
services:
  bookclub-server:
    environment:
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
    volumes:
      - prometheus-multiproc:/tmp/prometheus_multiproc
    command: >
      gunicorn -w 4
      -k uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8010
      book_club.server.server_main:server

volumes:
  prometheus-multiproc:
```

**Entrypoint script:**
```bash
#!/bin/bash
# Clean old metrics
rm -rf ${PROMETHEUS_MULTIPROC_DIR}/*.db

# Start server
exec gunicorn -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8010 \
  book_club.server.server_main:server
```

### Step 4: Update /metrics Endpoint

Already configured in `server_main.py`:

```python
@server.get("/metrics")
async def metrics():
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        # Multiprocess mode
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
    else:
        # Single-process mode
        data = generate_latest(REGISTRY)
    return Response(data, media_type=CONTENT_TYPE_LATEST)
```

### Step 5: Configure Prometheus

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'bookclub-server'
    scrape_interval: 15s
    static_configs:
      - targets: ['bookclub-server:8010']
    metric_relabel_configs:
      # Keep execution timing metrics
      - source_labels: [__name__]
        regex: '(.*_book_club_.*)|(.*_seconds)|(.*_calls_total)'
        action: keep
```

### Step 6: Create Grafana Dashboard

**Panel 1: P95 Latency**
```json
{
  "title": "P95 API Latency",
  "targets": [{
    "expr": "histogram_quantile(0.95, sum(rate(api_book_club_server_server_main_${function}_seconds_bucket{status=\"ok\"}[5m])) by (le))"
  }]
}
```

**Panel 2: Request Rate**
```json
{
  "title": "API Request Rate",
  "targets": [{
    "expr": "sum(rate(api_book_club_server_server_main_${function}_calls_total[5m])) by (status)"
  }]
}
```

**Panel 3: Error Rate**
```json
{
  "title": "Error Rate %",
  "targets": [{
    "expr": "sum(rate(api_book_club_server_server_main_${function}_calls_total{status=\"error\"}[5m])) / sum(rate(api_book_club_server_server_main_${function}_calls_total[5m])) * 100"
  }]
}
```

## Testing Strategy

### Unit Tests

**Test file structure:**
```
tests/
  observability/
    test_executiontimings.py  # Decorator tests
  api/
    test_endpoints.py          # Endpoint tests (check metrics indirectly)
```

**Example test:**
```python
from book_club.observability.ExecutionTimings import track_timing
from prometheus_client import generate_latest

def test_decorated_function_emits_metrics():
    @track_timing(namespace="test")
    def sample_fn():
        return "done"
    
    result = sample_fn()
    assert result == "done"
    
    # Check metrics
    metrics_output = generate_latest().decode()
    assert "test_" in metrics_output
    assert "sample_fn_seconds" in metrics_output
    assert 'status="ok"' in metrics_output
```

### Integration Tests

**Test decorated endpoints:**
```python
import pytest
from fastapi.testclient import TestClient
from book_club.server.server_main import server

@pytest.fixture
def client():
    return TestClient(server)

def test_health_endpoint_tracked(client):
    # Call endpoint
    response = client.get("/health")
    assert response.status_code == 200
    
    # Verify metrics endpoint includes timing
    metrics_response = client.get("/metrics")
    metrics = metrics_response.text
    
    # Check for health endpoint metrics
    assert "server_book_club" in metrics
    # Note: Exact metric name depends on decorator placement
```

### Load Testing

**Verify metrics under load:**
```bash
# Install hey (load testing tool)
# macOS: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Generate load
hey -n 10000 -c 50 http://localhost:8010/health

# Check Prometheus for rate increase
curl 'http://localhost:9090/api/v1/query?query=rate(server_book_club_server_server_main_health_calls_total[1m])'
```

## Common Patterns

### Pattern 1: API Endpoint Decoration

```python
@server.post("/ingest")
@track_timing(namespace="api")
async def ingest(data: dict, trace_id: str = None) -> dict:
    # Business logic
    return {"status": "ingested", "count": len(data)}
```

**Metrics:**
- `api_book_club_server_server_main_ingest_seconds{status="ok"}`
- `api_book_club_server_server_main_ingest_calls_total{status="ok"}`
- `api_book_club_server_server_main_ingest_seconds_bucket`

### Pattern 2: Database Layer

```python
class DatabaseService:
    @track_timing(namespace="db")
    async def fetch_user(self, user_id: int):
        # Database query
        return await db.query("SELECT * FROM users WHERE id = ?", user_id)
    
    @track_timing(namespace="db")
    async def save_user(self, user: dict):
        # Database insert/update
        return await db.execute("INSERT INTO users ...", user)
```

### Pattern 3: External API Calls

```python
@track_timing(namespace="external")
async def call_llm_api(prompt: str, _trace_id: str = None):
    try:
        response = await httpx.post(
            "https://api.openai.com/v1/completions",
            json={"prompt": prompt}
        )
        return response.json()
    except httpx.HTTPError:
        # Automatically tracked as status="error"
        raise
```

### Pattern 4: Background Jobs

```python
@track_timing(namespace="worker")
def process_queue_item(item: dict):
    # Process item
    return {"status": "processed", "item_id": item["id"]}

# Job runner
while True:
    item = queue.get()
    process_queue_item(item)  # Metrics tracked
```

### Pattern 5: Lifecycle Events

```python
@server.on_event("startup")
@track_timing(namespace="lifecycle")
async def startup():
    # Initialization
    await init_database()
    await load_models()

@server.on_event("shutdown")
@track_timing(namespace="lifecycle")
async def shutdown():
    # Cleanup
    await close_connections()
```

## Troubleshooting Workflows

### Workflow 1: Metrics Not Appearing

**Step 1:** Verify decorator is applied
```python
# Check your function
@track_timing(namespace="api")  # ✅ Decorator present
async def my_endpoint():
    pass
```

**Step 2:** Call the function at least once
```bash
curl http://localhost:8010/my_endpoint
```

**Step 3:** Check /metrics endpoint
```bash
curl http://localhost:8010/metrics | grep "my_endpoint"
```

**Step 4:** Check Prometheus target health
```bash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="bookclub-server")'
```

### Workflow 2: Multiprocess Metrics Aggregation

**Step 1:** Verify environment variable
```bash
echo $PROMETHEUS_MULTIPROC_DIR
# Should output: /tmp/prometheus_multiproc (or your path)
```

**Step 2:** Check worker metric files
```bash
ls -la $PROMETHEUS_MULTIPROC_DIR/
# Should see multiple .db files (one per worker)
```

**Step 3:** Verify aggregation in /metrics
```bash
curl http://localhost:8010/metrics | grep "_calls_total"
# Counters should be summed across workers
```

**Step 4:** Clean and restart if needed
```bash
rm -rf $PROMETHEUS_MULTIPROC_DIR/*.db
# Restart server
```

### Workflow 3: High Cardinality Issues

**Symptom:** Prometheus slow, high memory usage

**Step 1:** Check cardinality
```bash
curl http://localhost:9090/api/v1/label/__name__/values | jq '.data | length'
```

**Step 2:** Identify problematic metrics
```promql
# In Prometheus UI
topk(10, count by (__name__)({__name__=~".*book_club.*"}))
```

**Step 3:** Review decorator usage
```python
# ❌ BAD: High cardinality
@track_timing(namespace=f"user_{user_id}")  # Creates metric per user!

# ✅ GOOD: Low cardinality
@track_timing(namespace="api")  # Single metric
def process_user(user_id: int):
    pass
```

### Workflow 4: Performance Overhead

**Step 1:** Measure overhead
```python
import time

# Without decorator
start = time.perf_counter()
for _ in range(10000):
    my_function()
baseline = time.perf_counter() - start

# With decorator
@track_timing(namespace="test")
def my_function():
    pass

start = time.perf_counter()
for _ in range(10000):
    my_function()
with_tracking = time.perf_counter() - start

overhead = (with_tracking - baseline) / baseline * 100
print(f"Overhead: {overhead:.2f}%")
```

**Step 2:** Optimize if needed
```python
# Only track slow/critical functions
@track_timing(namespace="api")  # Keep for endpoints
async def slow_endpoint():
    pass

# Skip for hot paths
def fast_utility():  # No decorator for microsecond functions
    pass
```

## Alerting Setup

### Alert 1: High Error Rate

```yaml
# prometheus/alerts.yml
groups:
  - name: execution_timings
    rules:
      - alert: HighErrorRate
        expr: >
          sum(rate(api_book_club_server_server_main_ingest_calls_total{status="error"}[5m]))
          / sum(rate(api_book_club_server_server_main_ingest_calls_total[5m]))
          > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on ingest endpoint"
          description: "Error rate is {{ $value | humanizePercentage }}"
```

### Alert 2: High Latency

```yaml
- alert: HighP95Latency
  expr: >
    histogram_quantile(0.95,
      sum(rate(api_book_club_server_server_main_ingest_seconds_bucket{status="ok"}[5m])) by (le)
    ) > 1.0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "P95 latency above 1 second"
    description: "P95 latency is {{ $value }}s"
```

### Alert 3: Endpoint Downtime

```yaml
- alert: EndpointDown
  expr: >
    sum(rate(api_book_club_server_server_main_ingest_calls_total[5m])) == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Ingest endpoint receiving no traffic"
    description: "No requests in the last 5 minutes"
```

## Performance Benchmarks

### Expected Overhead

Based on internal testing:

| Function Duration | Overhead   | Impact       |
|-------------------|------------|--------------|
| < 1ms             | ~5-10%     | Noticeable   |
| 1-10ms            | ~1-2%      | Minimal      |
| 10-100ms          | ~0.1-0.5%  | Negligible   |
| > 100ms           | < 0.1%     | None         |

**Recommendation:** Only decorate functions with expected duration > 1ms.

### Metrics Storage

| Component      | Storage per metric/day | Notes                          |
|----------------|------------------------|--------------------------------|
| Gauge          | ~1 KB                  | Last value only                |
| Counter        | ~2 KB                  | Cumulative total               |
| Histogram      | ~10 KB                 | Multiple buckets + sum + count |

**Total per decorated function:** ~13 KB/day (assuming 15s scrape interval)

## Make Commands

### Add Convenience Targets

```makefile
# Add to Makefile

.PHONY: verify-metrics
verify-metrics: ## Verify execution timing metrics are working
	@echo "🔍 Verifying execution timing metrics..."
	@echo ""
	@echo "1️⃣  Starting server..."
	@$(UV) run uvicorn book_club.server.server_main:server --host 0.0.0.0 --port 8010 &
	@sleep 2
	@echo "✅ Server started"
	@echo ""
	@echo "2️⃣  Generating traffic..."
	@curl -s http://localhost:8010/health > /dev/null
	@echo "✅ Traffic generated"
	@echo ""
	@echo "3️⃣  Checking metrics..."
	@METRICS=$$(curl -s http://localhost:8010/metrics | grep "server_book_club" | grep "_seconds{" | wc -l); \
	if [ "$$METRICS" -gt 0 ]; then \
		echo "✅ Found $$METRICS execution timing metric(s)"; \
		curl -s http://localhost:8010/metrics | grep "server_book_club" | grep "_seconds{" | head -5; \
	else \
		echo "❌ No execution timing metrics found"; \
		exit 1; \
	fi
	@echo ""
	@echo "🎉 Execution timing metrics verified!"
	@pkill -f "uvicorn book_club.server.server_main"

.PHONY: test-executiontimings
test-executiontimings: ## Run execution timings unit tests
	@$(UV) run pytest tests/observability/test_executiontimings.py -v

.PHONY: bench-overhead
bench-overhead: ## Benchmark decorator overhead
	@echo "🔬 Benchmarking decorator overhead..."
	@$(UV) run python -m tests.observability.bench_executiontimings
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Metrics Tests
on: [push, pull_request]

jobs:
  test-metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run execution timing tests
        run: |
          make test-executiontimings
      
      - name: Verify metrics endpoint
        run: |
          make verify-metrics
      
      - name: Check for high-cardinality issues
        run: |
          # Fail if too many unique metric names
          METRIC_COUNT=$(curl -s http://localhost:8010/metrics | grep "^server_book_club" | wc -l)
          if [ "$METRIC_COUNT" -gt 100 ]; then
            echo "❌ Too many metrics ($METRIC_COUNT). Possible high-cardinality issue."
            exit 1
          fi
          echo "✅ Metric count OK ($METRIC_COUNT)"
```

## See Also

- [Execution Timings Documentation](./execution_timings.md) - Complete reference
- [Test Metrics Documentation](./test_metrics.md) - Test execution metrics
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
