# Data Purge Guide

## Overview

The `make purge-old-data` command provides a safe way to clean all observability data while preserving configurations, dashboards, and datasource definitions. This is useful for:

- Starting fresh after testing
- Cleaning up badly formatted data points
- Removing old unused artifacts/labels
- Freeing disk space

## Usage

```bash
make purge-old-data
```

The command will prompt for confirmation before proceeding.

## What Gets Deleted

### ✅ Data (Deleted)

1. **Log Files**
   - `logs/*.log` - All development logs
   - `logs/pytest_failures.log` - Test failure logs
   - `src/book_club/app/logs/*.log` - App runtime logs
   - `src/book_club/server/logs/*.log` - Server runtime logs

2. **Prometheus Data**
   - `observability/prometheus/data/*` - All metrics history
   - Scrape data, WAL segments, TSDB blocks

3. **Loki Data**
   - `observability/loki/data/*` - All log history
   - Chunks, indexes, ingester state

4. **Pushgateway Metrics**
   - All pushed metrics cleared on restart

5. **Qdrant Data**
   - `data/qdrant/*` - All vector database data
   - Collections and indexes

6. **Grafana Session Data**
   - `observability/grafana/data/grafana.db*` - User sessions
   - Login state, temporary data

### ❌ Configuration (Preserved)

1. **Alloy Configuration**
   - `observability/alloy/config.alloy` - Log collection rules
   - Processing pipelines, label extraction

2. **Prometheus Configuration**
   - `observability/prometheus/prometheus.yml` - Scrape configs
   - Target definitions, rules

3. **Loki Configuration**
   - `observability/loki/config.yml` - Storage settings
   - Retention policies, ingestion limits

4. **Grafana Assets**
   - `observability/grafana/dashboards/*.json` - All dashboards
   - `observability/grafana/provisioning/` - Datasource configs
   - `observability/grafana/grafana.ini` - Grafana settings

5. **Docker Compose**
   - `docker-compose.yml` - Service definitions
   - Volume mounts, network configs

## Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1️⃣  Display confirmation prompt                                  │
│    • Lists what will be deleted                                 │
│    • Lists what will be preserved                               │
│    • Requires [y/N] confirmation                                │
└────────────────────────────┬────────────────────────────────────┘
                             │ [User confirms]
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2️⃣  Stop services (graceful shutdown)                            │
│    • Prometheus, Loki, Pushgateway                              │
│    • Qdrant, Grafana, Alloy                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3️⃣  Clean log files                                              │
│    • rm -rf logs/*.log                                          │
│    • rm -rf src/book_club/app/logs/*.log                        │
│    • rm -rf src/book_club/server/logs/*.log                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4️⃣  Clean Prometheus data                                        │
│    • rm -rf observability/prometheus/data/*                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5️⃣  Clean Loki data                                              │
│    • rm -rf observability/loki/data/*                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6️⃣  Clean Qdrant data                                            │
│    • rm -rf data/qdrant/*                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7️⃣  Clean Grafana session data                                   │
│    • rm -rf observability/grafana/data/grafana.db*              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8️⃣  Restart services                                             │
│    • docker compose up -d [services]                            │
│    • Services start with clean data directories                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9️⃣  Verify services are healthy                                  │
│    • Check Prometheus: curl http://localhost:9090              │
│    • Check Loki: curl http://localhost:3100/ready              │
│    • Check Pushgateway: curl http://localhost:9091/metrics     │
│    • Check Grafana: curl http://localhost:3000/api/health      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                      ✅ Clean slate!
```

## Example Run

```bash
$ make purge-old-data

🧹 Purging old observability data...

⚠️  This will delete:
   • All log files
   • All Prometheus metrics history
   • All Loki log history
   • All Pushgateway metrics
   • All Qdrant vector data
   • Grafana session data

✅ This will keep:
   • All configuration files
   • All Grafana dashboards
   • All datasource definitions

Are you sure? [y/N] y

1️⃣  Stopping services...
 Container prometheus  Stopping
 Container loki  Stopping
 Container pushgateway  Stopping
 Container qdrant  Stopping
 Container grafana  Stopping
 Container alloy  Stopping
✓ Services stopped

2️⃣  Cleaning log files...
   ✅ Cleaned logs/
   ✅ Cleaned app logs/
   ✅ Cleaned server logs/

3️⃣  Cleaning Prometheus data...
   ✅ Cleaned Prometheus data

4️⃣  Cleaning Loki data...
   ✅ Cleaned Loki data

5️⃣  Cleaning Qdrant data...
   ✅ Cleaned Qdrant data

6️⃣  Cleaning Grafana session data...
   ✅ Cleaned Grafana sessions

7️⃣  Restarting services...
 Container prometheus  Started
 Container loki  Started
 Container pushgateway  Started
 Container qdrant  Started
 Container grafana  Started
 Container alloy  Started

8️⃣  Waiting for services to be ready...

9️⃣  Verifying clean state...
   ✅ Prometheus running
   ✅ Loki running
   ✅ Pushgateway running
   ✅ Grafana running

🎉 Observability data purged successfully!

📊 Access points:
   • Grafana:     http://localhost:3000
   • Prometheus:  http://localhost:9090
   • Loki:        http://localhost:3100
   • Pushgateway: http://localhost:9091
```

## Post-Purge Actions

After purging data, the observability stack will be in a clean state:

### 1. Verify Services
```bash
# Quick health check
make verify-quick

# Full observability pipeline check
make verify-observability
```

### 2. Generate Fresh Data
```bash
# Run tests and push metrics
make push-tests

# Run application to generate logs
uv run -m book_club.__main__
```

### 3. Check Grafana
1. Open http://localhost:3000
2. Log in (you may need to log in again after session purge)
3. Your dashboards should still be there
4. No old data in visualizations

### 4. Verify Clean Metrics
```bash
# Check Prometheus has no old data
curl 'http://localhost:9090/api/v1/query?query=up'

# Check Loki has no old logs
curl -H "X-Scope-OrgID: local" \
  'http://localhost:3100/loki/api/v1/labels'
```

## Troubleshooting

### Services Don't Start After Purge

**Problem:** Services fail to start after data deletion

**Solution:**
```bash
# Check service logs
docker compose logs prometheus
docker compose logs loki

# Recreate data directories with correct permissions
mkdir -p observability/prometheus/data
mkdir -p observability/loki/data
mkdir -p data/qdrant

# Restart services
docker compose up -d
```

### Grafana Dashboards Missing

**Problem:** Dashboards disappeared after purge

**Cause:** Dashboards were stored in Grafana's database (grafana.db) instead of provisioned

**Prevention:**
- Store dashboards as JSON in `observability/grafana/dashboards/`
- Use dashboard provisioning (see Grafana docs)

**Recovery:**
- Restore dashboards from JSON files
- Import manually or via provisioning

### Permission Errors

**Problem:** Cannot delete files due to permission errors

**Solution:**
```bash
# Check ownership
ls -la observability/prometheus/data/

# Fix permissions if needed
sudo chown -R $USER:$USER observability/
sudo chown -R $USER:$USER data/
sudo chown -R $USER:$USER logs/

# Retry purge
make purge-old-data
```

## When to Use

### ✅ Good Use Cases

1. **Development/Testing**
   - Clean slate between test runs
   - Remove test metrics and logs

2. **Data Quality Issues**
   - Badly formatted metrics
   - Incorrect labels
   - Duplicate data

3. **Disk Space Management**
   - Free up space quickly
   - Remove old data before archiving

4. **Fresh Start**
   - After configuration changes
   - Before demo/presentation

### ❌ Avoid Using When

1. **Production Environment**
   - Use proper retention policies instead
   - Data loss could impact operations

2. **Debugging Issues**
   - May need historical data
   - Use selective queries instead

3. **Before Backup**
   - Export important data first
   - Consider archiving instead

## Related Commands

| Command | Purpose |
|---------|---------|
| `make purge-old-data` | Clean all observability data |
| `make verify-observability` | Test full pipeline |
| `make verify-quick` | Quick service health check |
| `make push-tests` | Generate fresh test metrics |
| `docker compose down -v` | Stop + remove volumes (nuclear option) |

## Safety Features

1. **Confirmation Prompt**
   - Requires explicit [y/N] confirmation
   - Shows what will be deleted
   - Shows what will be preserved

2. **Graceful Service Shutdown**
   - Stops services before deleting data
   - Prevents data corruption

3. **Configuration Preservation**
   - Never touches config files
   - Dashboards remain intact
   - Datasources preserved

4. **Service Verification**
   - Checks all services after restart
   - Reports health status
   - Provides access URLs

## Disk Space Recovered

Typical space freed (depends on usage):

- **Prometheus data**: 100MB - 10GB
- **Loki data**: 50MB - 5GB
- **Qdrant data**: Variable (depends on vectors)
- **Log files**: 1MB - 100MB
- **Grafana sessions**: <1MB

**Total**: Usually 200MB - 15GB

## See Also

- [Logs Monitoring with Alloy](./logs-monitoring-with-alloy.md)
- [Main Documentation](./README.md)
