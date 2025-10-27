# Documentation Index

## Observability & Monitoring

### [Logs Monitoring with Alloy](./logs-monitoring-with-alloy.md)
Comprehensive guide to the log collection and monitoring setup using Grafana Alloy and Loki:
- Architecture overview
- Log source configuration
- Alloy processing pipelines
- Pytest failure logging
- LogQL query examples
- Troubleshooting guide

## Quick Reference

### Data Management

**Purge all observability data:**
```bash
make purge-old-data
```
This removes all metrics, logs, and traces while keeping configurations and dashboards intact.

**Push test metrics to Pushgateway:**
```bash
make push-tests
```

**Verify observability stack:**
```bash
make verify-observability
```

### Access Points

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Pushgateway**: http://localhost:9091
- **Alloy UI**: http://localhost:12345

### Common Tasks

#### View Logs in Grafana
1. Open Grafana: http://localhost:3000
2. Navigate to **Explore** (compass icon)
3. Select **Loki** datasource
4. Query examples:
   - All pytest failures: `{source="pytest", event="test_failure"}`
   - Server errors: `{filename="server_main.py", level="ERROR"}`

#### Query Prometheus Metrics
```bash
# Test metrics count
curl -s 'http://localhost:9090/api/v1/query?query=count(test_duration_seconds)'

# Failed test metrics
curl -s 'http://localhost:9090/api/v1/query?query=test_outcome{outcome="failed"}'
```

#### Query Loki Logs
```bash
# Get labels (requires X-Scope-OrgID header)
curl -H "X-Scope-OrgID: local" \
  "http://localhost:3100/loki/api/v1/labels"

# Query pytest failures
curl -H "X-Scope-OrgID: local" \
  "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={source="pytest", event="test_failure"}'
```

## Development

### Running Tests
```bash
# Run all tests (parallel with xdist)
make push-tests

# Run specific test
uv run pytest tests/observability/test_monitoring.py -v

# Run without xdist
uv run pytest -o addopts="" tests/
```

### Log File Locations

| Log Type | Host Path | Container Path (Alloy) |
|----------|-----------|------------------------|
| Development logs | `./logs/` | `/development_logs/` |
| Pytest failures | `./logs/pytest_failures.log` | `/development_logs/pytest_failures.log` |
| App logs | `./src/book_club/app/logs/` | `/app_logs/` |
| Server logs | `./src/book_club/server/logs/` | `/server_logs/` |

### Configuration Files

| Component | Configuration File |
|-----------|-------------------|
| Alloy | `observability/alloy/config.alloy` |
| Loki | `observability/loki/config.yml` |
| Prometheus | `observability/prometheus/prometheus.yml` |
| Grafana | `observability/grafana/provisioning/` |

## Troubleshooting

### Services Not Starting
```bash
# Check service status
docker compose ps

# View logs for specific service
docker compose logs -f alloy
docker compose logs -f loki
docker compose logs -f prometheus
```

### Logs Not Appearing
```bash
# Check Alloy is tailing files
docker compose logs alloy | grep "tail routine"

# Verify Loki connectivity
curl -H "X-Scope-OrgID: local" http://localhost:3100/ready
```

### Clean Slate
```bash
# Stop all services
docker compose down

# Purge all data
make purge-old-data

# Start fresh
docker compose up -d
```

## Project Structure

```
BookClub_local_poc/
├── docs/                           # Documentation
│   ├── logs-monitoring-with-alloy.md
│   └── README.md (this file)
├── logs/                           # Development logs
│   ├── main.log                    # Application logs
│   └── pytest_failures.log         # Test failure logs (JSON)
├── observability/                  # Observability stack
│   ├── alloy/
│   │   └── config.alloy           # Log collection config
│   ├── grafana/
│   │   ├── dashboards/            # Dashboard JSON files
│   │   └── provisioning/          # Datasource configs
│   ├── loki/
│   │   ├── config.yml             # Loki configuration
│   │   └── data/                  # Log storage (data)
│   └── prometheus/
│       ├── prometheus.yml          # Scrape configs
│       └── data/                   # Metrics storage (data)
├── src/book_club/                  # Application code
│   ├── app/                        # Frontend app
│   │   └── logs/                   # App runtime logs
│   ├── server/                     # Backend server
│   │   └── logs/                   # Server runtime logs
│   └── observability/              # Observability utilities
├── tests/                          # Test suite
│   ├── conftest.py                 # Pytest config (metrics & logging)
│   ├── integration/                # Integration tests
│   └── observability/              # Observability tests
├── docker-compose.yml              # Service definitions
├── Makefile                        # Development commands
└── pyproject.toml                  # Python project config
```

## Contributing

When adding new features that involve logging or metrics:

1. **Add structured logging** with consistent format
2. **Update Alloy config** if new log sources are added
3. **Add test metrics** using the pytest plugin
4. **Document** in this folder
5. **Verify** with `make verify-observability`

## References

- [Grafana Alloy Documentation](https://grafana.com/docs/alloy/latest/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [pytest Documentation](https://docs.pytest.org/)
