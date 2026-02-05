# Logs Monitoring with Alloy

## Overview

This project uses **Grafana Alloy** as a universal log collector that ingests logs from various sources and forwards them to **Loki** for storage and querying. Alloy supports multiple log formats and provides powerful processing pipelines.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Application Logs                                                │
│  • logs/main.log (development, structured format)              │
│  • logs/pytest_failures.log (test failures, JSON format)       │
│  • src/book_club/app/logs/*.log (app runtime logs)            │
│  • src/book_club/preprocessing_server/logs/*.log (server logs) │
│  • Docker container logs (loki.source.docker + socket)        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Grafana Alloy (Universal Log Collector)                        │
│  • File tailing with position tracking                         │
│  • Log parsing (JSON, structured text, regex)                  │
│  • Label extraction and enrichment                             │
│  • Multi-tenant support (tenant_id = "local")                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Grafana Loki (Log Storage)                                     │
│  • Multi-tenant mode (X-Scope-OrgID: local)                    │
│  • Indexed by labels (level, source, event, filename, etc.)    │
│  • Full-text search with LogQL                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Grafana (Visualization)                                        │
│  • Explore view for log queries                                │
│  • Dashboard panels with log streams                           │
│  • Alert rules based on log patterns                           │
└─────────────────────────────────────────────────────────────────┘
```

## Log Sources and Formats

### 1. **Structured Development Logs** (logs/main.log)

**Format:**
```
2025-10-27 14:30:15 - book_club.main - INFO - main.py - 42 - main - 12345 - 67890 - MainThread - Application started
```

**Pattern:**
```
<timestamp> - <logger> - <level> - <filename> - <lineno> - <funcName> - <process> - <thread> - <threadName> - <message>
```

**Alloy Processing:**
- Parsed via regex in `loki.process.structured_logs`
- Extracted labels: `level`, `logger`, `filename`, `funcName`

### 2. **Pytest Failure Logs** (logs/pytest_failures.log)

**Format:** JSON (one object per line)
```json
{
  "timestamp": "2025-10-27T22:55:31.204181Z",
  "level": "ERROR",
  "event": "test_failure",
  "source": "pytest",
  "test_name": "tests/test_example.py::test_failing",
  "file": "tests/test_example.py",
  "outcome": "failed",
  "duration": 0.0004880249980487861,
  "short_error": "test_example.py:9: AssertionError",
  "failure_message": "def test_failing():\n>   assert False\nE   AssertionError\n...",
  "test_type": "unspecified"
}
```

**Alloy Processing:**
- Parsed via JSON in `loki.process.pytest_json`
- Extracted labels: `level`, `event`, `source`, `outcome`
- Full JSON available in log line content

### 3. **App Runtime Logs** (src/book_club/app/logs/*.log)

**Format:** Structured (similar to development logs)

**Alloy Processing:**
- Parsed via `loki.process.add_new_label`
- Standard structured log parsing

### 4. **Server Runtime Logs** (file + stdout)

**Paths:** `src/book_club/preprocessing_server/logs/*.log` (file) and Docker stdout (preferred in Grafana).

**Format:** Structured (similar to development logs). The server logs to both a file and stdout; Alloy collects stdout via `loki.source.docker`, which adds a `service_name` label from the container name.

**Alloy Processing:**
- File: `loki.source.file` + `loki.process.add_new_label` when the log file exists.
- Stdout: `discovery.docker` + `loki.source.docker` with `service_name` from container name (e.g. `bookclub-preprocessing-server`).

### 5. **Docker Container Logs**

**Format:** JSON (Docker's native format). Collected via `loki.source.docker` using the Docker socket so each stream gets a `service_name` label (container name without leading slash).

**Alloy Processing:**
- `discovery.docker` discovers containers; `discovery.relabel` exports a rule to set `service_name` from `__meta_docker_container_name`.
- `loki.source.docker` tails container logs and applies the relabel rules; forwards to Loki.

## Alloy Configuration

### File Location
```
observability/alloy/config.alloy
```

### Key Components

#### 1. File Matching (Discovery)
```hcl
local.file_match "pytest_logs" {
  path_targets = [{"__path__" = "/development_logs/pytest_failures.log"}]
  sync_period = "1s"
}
```
- Discovers files matching patterns
- Monitors for new files
- `sync_period`: How often to check for new files

#### 2. File Tailing (Reading)
```hcl
loki.source.file "pytest_logs" {
  targets = local.file_match.pytest_logs.targets
  forward_to = [loki.process.pytest_json.receiver]
}
```
- Tails files with position tracking
- Resumes from last read position after restart
- Forwards log lines to processing pipeline

#### 3. Log Processing (Parsing & Labeling)
```hcl
loki.process "pytest_json" {
  stage.json {
    expressions = {
      extracted_level  = "level",
      extracted_event  = "event",
      extracted_source = "source",
      test_name        = "test_name",
      test_file        = "file",
      outcome          = "outcome",
      short_error      = "short_error",
    }
  }
  
  stage.labels {
    values = {
      level  = "extracted_level",
      event  = "extracted_event",
      source = "extracted_source",
      outcome = "outcome",
    }
  }
  
  forward_to = [loki.write.local.receiver]
}
```
- **stage.json**: Extract fields from JSON logs
- **stage.regex**: Extract fields from structured text logs
- **stage.labels**: Convert extracted fields to Loki labels

#### 4. Writing to Loki
```hcl
loki.write "local" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
    tenant_id = "local"
  }
}
```
- Writes to Loki with tenant ID
- Handles batching and retries

## Volume Mounts (docker-compose.yml)

```yaml
alloy:
  volumes:
    - ./observability/alloy/config.alloy:/etc/alloy/config.alloy:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/log:/var/log:ro
    - ./logs:/development_logs/                    # Host: logs/ → Container: /development_logs/
    - ./src/book_club/app/logs:/app_logs/          # App runtime logs
    - /var/run/docker.sock:/var/run/docker.sock:ro # For loki.source.docker (container names)
    - ./src/book_club/preprocessing_server/logs:/preprocessing_server/
```

**Important:** 
- Host paths on the left
- Container paths on the right (used in Alloy config)
- `:ro` means read-only

## Querying Logs in Grafana

### Access Loki
1. Navigate to Grafana: http://localhost:3000
2. Go to **Explore** (compass icon)
3. Select **Loki** data source

### Example Queries (LogQL)

#### 1. Preprocessing server logs (Docker stdout)
```logql
{job="docker", service_name="bookclub-preprocessing-server"}
```
Use this in Explore to see logs from the FastAPI preprocessing server. The server logs to stdout; Alloy collects them via `loki.source.docker` and labels by container name.

#### 2. All pytest failures
```logql
{source="pytest", event="test_failure"}
```

#### 3. Failed tests only
```logql
{source="pytest", outcome="failed"}
```

#### 4. Errors from a specific file
```logql
{filename="server_main.py", level="ERROR"}
```

#### 5. Filter by message content
```logql
{source="pytest"} |= "AssertionError"
```

#### 6. Count failures over time
```logql
sum(count_over_time({source="pytest", outcome="failed"}[5m]))
```

#### 7. Extract JSON fields
```logql
{source="pytest"} | json | short_error != ""
```

### Query Operators

- `|=` : Line contains string
- `!=` : Line does not contain string
- `|~ "regex"` : Line matches regex
- `!~ "regex"` : Line does not match regex
- `| json` : Parse line as JSON
- `| logfmt` : Parse line as logfmt
- `| regexp "(?P<field>pattern)"` : Extract with regex

## Loki Multi-Tenancy

**Important:** Loki runs in multi-tenant mode with tenant ID `"local"`.

### API Queries
All direct API queries to Loki **must include** the `X-Scope-OrgID` header:
```bash
curl -H "X-Scope-OrgID: local" \
  "http://localhost:3100/loki/api/v1/labels"
```

### Programmatic Access
If using LokiHandler directly in application code:
```python
import requests

response = requests.post(
    "http://localhost:3100/loki/api/v1/push",
    headers={"X-Scope-OrgID": "local", "Content-Type": "application/json"},
    json=payload
)
```

## Pytest Test Failure Logging

### How It Works

1. **Test Execution:** When a test fails, pytest hook `pytest_runtest_makereport` is triggered
2. **Failure Capture:** `_log_test_failure()` in `tests/conftest.py` extracts failure details
3. **JSON Serialization:** Failure is formatted as JSON with rich metadata
4. **File Logging:** JSON written to `logs/pytest_failures.log`
5. **Alloy Ingestion:** Alloy tails the file and parses JSON
6. **Loki Storage:** Structured log stored with labels (source, event, outcome, level)
7. **Grafana Query:** Searchable via LogQL with full context

### Failure Log Fields

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | ISO 8601 timestamp | `2025-10-27T22:55:31.204181Z` |
| `level` | Log level (always ERROR) | `ERROR` |
| `event` | Event type | `test_failure` |
| `source` | Log source | `pytest` |
| `test_name` | Full test node ID | `tests/test_example.py::test_foo` |
| `file` | Test file path | `tests/test_example.py` |
| `outcome` | Test result | `failed` |
| `duration` | Test execution time (seconds) | `0.000488` |
| `short_error` | Last line of error | `test_example.py:9: AssertionError` |
| `failure_message` | Full traceback (truncated at 2000 chars) | `def test_foo():\n>   assert False\n...` |
| `test_type` | Test marker (if any) | `integration` |

### Querying Test Failures

**View all failures:**
```logql
{source="pytest", event="test_failure"}
```

**View failures for specific test file:**
```logql
{source="pytest"} | json | file="tests/integration/test_server.py"
```

**Extract short error messages:**
```logql
{source="pytest"} | json | line_format "{{.test_name}}: {{.short_error}}"
```

## Adding New Log Sources

### Step 1: Add File Match Pattern
```hcl
local.file_match "my_logs" {
  path_targets = [{"__path__" = "/my_logs/*.log"}]
  sync_period = "1s"
}
```

### Step 2: Add File Source
```hcl
loki.source.file "my_logs" {
  targets = local.file_match.my_logs.targets
  forward_to = [loki.process.my_processor.receiver]
}
```

### Step 3: Add Processing Pipeline
```hcl
loki.process "my_processor" {
  // For JSON logs
  stage.json {
    expressions = {
      level = "level",
      msg   = "message",
    }
  }
  
  // For structured logs
  stage.regex {
    expression = "^(?P<timestamp>[^ ]+) (?P<level>[^ ]+) (?P<message>.*)$"
  }
  
  stage.labels {
    values = {
      level = "level",
    }
  }
  
  forward_to = [loki.write.local.receiver]
}
```

### Step 4: Add Volume Mount in docker-compose.yml
```yaml
alloy:
  volumes:
    - ./my_logs:/my_logs/:ro
```

### Step 5: Restart Alloy
```bash
docker compose restart alloy
```

## Troubleshooting

### Logs Not Appearing in Loki

1. **Check Alloy is tailing the file:**
   ```bash
   docker compose logs alloy | grep "tail routine"
   ```
   Expected: `tail routine: started ... path=/development_logs/pytest_failures.log`

2. **Check for Alloy errors:**
   ```bash
   docker compose logs alloy | grep -i error
   ```

3. **Verify Loki is receiving data:**
   ```bash
   curl -H "X-Scope-OrgID: local" \
     "http://localhost:3100/loki/api/v1/labels"
   ```
   Expected: JSON with list of labels

4. **Check Alloy config syntax:**
   ```bash
   docker compose exec alloy alloy fmt --check /etc/alloy/config.alloy
   ```

### Labels Not Extracted

1. **Verify log format matches regex/json:**
   - Check actual log line format
   - Test regex at https://regex101.com
   - Validate JSON with `jq`

2. **Check Alloy processing stages:**
   ```bash
   docker compose logs alloy | grep -i "stage"
   ```

3. **Enable debug output in Alloy:**
   ```hcl
   stage.output {
     source = "output"
   }
   ```

### Permission Errors

If Alloy cannot read log files:
```bash
# Check file permissions
ls -l logs/*.log

# Ensure Alloy user can read (may need 644 or 666)
chmod 644 logs/*.log
```

## Performance Considerations

### Label Cardinality
- Keep label cardinality low (< 10 labels per log stream)
- High cardinality labels (like `test_name`) should be in log content, not labels
- Use labels for filtering, not for unique identification

### Log Volume
- Alloy buffers logs in memory before sending to Loki
- Large log volumes may require tuning `batch_wait` and `batch_size`
- Consider log sampling for high-volume sources

### Retention
- Configure Loki retention in `observability/loki/config.yml`
- Default retention: determined by Loki config
- Adjust based on disk space and query requirements

## Best Practices

1. **Use structured logging in application code**
   - Consistent format makes parsing easier
   - Include correlation IDs (trace_id, span_id)

2. **Add context to log messages**
   - Who, what, when, where, why
   - Include relevant IDs and state

3. **Use appropriate log levels**
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Something unexpected but handled
   - ERROR: Error that needs attention
   - CRITICAL: System is unusable

4. **Keep log lines under 64KB**
   - Loki has a default limit of 256KB per line
   - Very large messages should be truncated or split

5. **Use labels for high-level filtering**
   - Good: `level`, `source`, `environment`
   - Bad: `user_id`, `request_id`, `session_id`

6. **Test log ingestion pipeline**
   - Verify logs reach Loki after config changes
   - Use `make verify-observability` to test end-to-end

## Related Documentation

- [Prometheus Metrics Setup](./metrics-setup.md) *(if exists)*
- [Grafana Dashboards](./grafana-dashboards.md) *(if exists)*
- [Observability Stack Verification](../README.md#observability)

## References

- [Grafana Alloy Documentation](https://grafana.com/docs/alloy/latest/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [LogQL Query Language](https://grafana.com/docs/loki/latest/query/)
- [Docker Logging Drivers](https://docs.docker.com/config/containers/logging/)
