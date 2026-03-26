# PDF Upload Metrics - RED Metrics & Throughput

## Overview

`IngestMetrics.py` provides Prometheus metrics for the `/upload-pdf` endpoint, implementing the RED method (Rate, Errors, Duration) plus domain-specific metrics for file size distribution and throughput tracking.

**Key Features:**
- **RED metrics** - Request rate, error rate, and duration histograms
- **File size tracking** - Histogram of uploaded PDF sizes
- **Throughput counter** - Total bytes uploaded over time
- **Status labelling** - All metrics labelled with `status="ok"` or `status="error"`
- **Gunicorn compatible** - Supports multiprocess mode with worker aggregation
- **Trace integration** - Exemplar support for linking to Tempo traces

## Metrics Exposed

All metrics use the `preprocessing_server_pdf_upload_` prefix:

| Metric | Type | Description |
|--------|------|-------------|
| `preprocessing_server_pdf_upload_requests_total{status}` | Counter | Total upload requests (RED: Rate + Errors) |
| `preprocessing_server_pdf_upload_duration_seconds{status}` | Histogram | Request duration in seconds (RED: Duration) |
| `preprocessing_server_pdf_upload_size_bytes{status}` | Histogram | Uploaded file size distribution |
| `preprocessing_server_pdf_upload_bytes_total{status}` | Counter | Total bytes uploaded (throughput) |

### Labels

- `status="ok"` - Successful uploads
- `status="error"` - Failed uploads (validation errors, storage errors, etc.)

### Histogram Buckets

**Duration buckets (seconds):**
```
0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30
```

**Size buckets (bytes):**
```
100KB, 500KB, 1MB, 2MB, 5MB, 10MB, 20MB, 50MB
```

## Usage

### In Code

```python
from book_club.observability.IngestMetrics import ingest_metrics

# Manual observation (if not using the endpoint decorator)
ingest_metrics.observe_upload(
    size_bytes=1024000,
    status="ok",
    duration_s=0.5,
    exemplar={"trace_id": "abc123"}  # Optional: for Tempo linking
)
```

### Automatic Tracking

The `/upload-pdf` endpoint automatically records metrics on every request. No additional configuration required.

## Demo & Traffic Generation

Make targets are provided for generating test traffic to verify dashboards and metrics flow.

### Generate Errors Only

```bash
# Generate 5 errors (default)
make demo-upload-errors

# Generate 10 errors
make demo-upload-errors ERR=10
```

### Generate Mixed Traffic

```bash
# Generate 5 successes + 5 errors (default)
make demo-upload-traffic

# Generate custom mix: 20 successes, 3 errors
make demo-upload-traffic OK=20 ERR=3
```

### Output Example

```
Generating mixed PDF upload traffic (5 success, 5 errors)...

.....xxxxx

Generated 5 successes and 5 errors

Current metrics:
  Total: 24 requests
  Success: 12 (50.0%)
  Errors: 12 (50.0%)

View in Grafana: http://localhost:3000/d/pdf-upload/pdf-upload-red-metrics-throughput
```

Legend:
- `.` (green) = successful upload
- `x` (red) = failed upload

## Grafana Dashboard

The **PDF Upload - RED Metrics & Throughput** dashboard provides:

### Row 1: RED Metrics
- **Request Rate** - Requests per second by status
- **Error Rate (%)** - Percentage of failed requests
- **Total Requests** - Cumulative request count
- **Total Errors** - Cumulative error count

### Row 2: Latency
- **Duration Percentiles** - p50, p95, p99 response times
- **p95 Latency** - Time series of 95th percentile
- **Average Duration** - Mean request duration
- **Duration Distribution** - Heatmap of response times

### Row 3: File Size & Throughput
- **File Size Distribution** - Histogram of uploaded file sizes
- **Average File Size** - Mean file size over time
- **p95 File Size** - 95th percentile file size
- **Upload Throughput** - Bytes per second
- **Total Bytes Uploaded** - Cumulative bytes (success vs error)

### Access

- **URL:** http://localhost:3000/d/pdf-upload/pdf-upload-red-metrics-throughput
- **Datasource:** Prometheus

## PromQL Examples

### Request Rate
```promql
sum by (status) (rate(preprocessing_server_pdf_upload_requests_total[$__rate_interval]))
```

### Error Rate Percentage
```promql
100 * sum(rate(preprocessing_server_pdf_upload_requests_total{status="error"}[$__rate_interval]))
    / sum(rate(preprocessing_server_pdf_upload_requests_total[$__rate_interval]))
```

### p95 Latency
```promql
histogram_quantile(0.95,
  sum(rate(preprocessing_server_pdf_upload_duration_seconds_bucket{status="ok"}[$__rate_interval])) by (le)
)
```

### Average File Size
```promql
sum(rate(preprocessing_server_pdf_upload_size_bytes_sum{status="ok"}[$__rate_interval]))
  / sum(rate(preprocessing_server_pdf_upload_size_bytes_count{status="ok"}[$__rate_interval]))
```

### Upload Throughput (bytes/sec)
```promql
sum(rate(preprocessing_server_pdf_upload_bytes_total{status="ok"}[$__rate_interval]))
```

## Architecture

```
┌─────────────────────┐
│   /upload-pdf       │
│   (FastAPI)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   IngestMetrics     │
│   observe_upload()  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   /metrics          │
│   (prometheus_client)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Prometheus        │────▶│   Grafana           │
│   :9090             │     │   :3000             │
└─────────────────────┘     └─────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PDF_STORAGE_DIR` | `/pdfs` | Directory to store uploaded PDFs |
| `MAX_PDF_SIZE_MB` | `50` | Maximum allowed file size in MB |
| `PROMETHEUS_MULTIPROC_DIR` | (unset) | Directory for multiprocess mode |

### Prometheus Scrape Config

```yaml
# observability/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'bookclub-preprocessing-server'
    metrics_path: /metrics
    static_configs:
      - targets: ['bookclub-preprocessing-server:8010']
```

## Troubleshooting

### Metrics Not Appearing

1. **Check endpoint is responding:**
   ```bash
   curl http://localhost:8010/metrics | grep preprocessing_server
   ```

2. **Check Prometheus target health:**
   ```bash
   curl -s http://localhost:9090/api/v1/targets | \
     python3 -c "import sys,json; d=json.load(sys.stdin); \
     [print(f\"{t['labels']['job']}: {t['health']}\") for t in d['data']['activeTargets']]"
   ```

3. **Query metrics directly:**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=preprocessing_server_pdf_upload_requests_total'
   ```

### Dashboard Shows No Data

1. **Check time range** - Adjust to "Last 5 minutes" or "Last 15 minutes"
2. **Generate traffic** - Run `make demo-upload-traffic` to populate metrics
3. **Verify dashboard mount** - Ensure `docker-compose.yml` mounts dashboards correctly:
   ```yaml
   volumes:
     - ./observability/dashboards:/var/lib/grafana/dashboards
   ```

### Multiprocess Mode (Gunicorn)

When running with multiple workers, set:

```bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p $PROMETHEUS_MULTIPROC_DIR
```

The metrics endpoint will automatically aggregate metrics across all workers.

## Related Documentation

- [Execution Timings](execution_timings.md) - Function-level performance tracking
- [Test Metrics](test_metrics.md) - Pytest metrics to Pushgateway
- [Logs Monitoring](logs-monitoring-with-alloy.md) - Log aggregation with Alloy/Loki
