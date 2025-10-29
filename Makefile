# ===== Book Club POC — uv-driven Makefile =====

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-builtin-rules
.DEFAULT_GOAL := help

UV := $(HOME)/.local/bin/uv
PY := .venv/bin/python
PIP := .venv/bin/pip

# -------- Targets --------

help: ## Show this help
	@echo ""
	@echo "════════════════════════════════════════════════════════════════════════════════"
	@echo "  📚 Book Club POC — Make Targets"
	@echo "════════════════════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "🔧 SETUP & ENVIRONMENT"
	@grep -E '^(ensure-uv|venv|deps-seed|lock|install|install-dev|setup|sync|sync-dev):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🚀 DEVELOPMENT"
	@grep -E '^(run|test|coverage|lint|fmt|typecheck|precommit):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📦 BUILD & CLEAN"
	@grep -E '^(clean|dist):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🧪 TESTING & METRICS"
	@grep -E '^(push-tests|verify-test-metrics|test-cleanup-behavior):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🐳 DOCKER COMPOSE"
	@grep -E '^(compose-install|compose-version|compose-switch):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📊 OBSERVABILITY VERIFICATION"
	@grep -E '^(verify-observability|verify-quick|verify-logs|verify-integration):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🧹 MAINTENANCE"
	@grep -E '^(purge-old-data):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "════════════════════════════════════════════════════════════════════════════════"
	@echo ""

ensure-uv: ## Install uv locally if not present
	@if ! command -v $(UV) >/dev/null 2>&1; then
		curl -Ls https://astral.sh/uv/install.sh | sh
		echo 'export PATH="$$HOME/.local/bin:$$PATH"' >> $$HOME/.zshrc
	fi
	@$(UV) --version

venv: ensure-uv ## Create or update .venv with Python 3.11
	@$(UV) venv .venv --python 3.11

deps-seed: ## Create requirements.in/dev.in if missing (one-time seed)
	@[ -f requirements.in ] || cat > requirements.in <<-'REQ'
	httpx==0.27.0
	pydantic==2.8.0
	rich==13.7.0
	REQ
	@[ -f requirements-dev.in ] || cat > requirements-dev.in <<-'REQ'
	pytest==8.2.0
	pytest-cov==5.0.0
	ruff==0.6.0
	mypy==1.11.0
	pre-commit==3.7.0
	REQ

lock: ensure-uv deps-seed ## Resolve & lock dependencies
	@$(UV) lock

install: venv lock ## Install from lockfiles into .venv
	@$(UV) sync
	@$(UV) run pre-commit install || true

install-dev: venv lock ## Install app + dev deps from lockfile into .venv
	@$(UV) sync --all-groups
	@$(UV) run pre-commit install || true

setup: install-dev ## Full setup (uv + venv + locked deps)
	@echo "✅ uv environment ready."

run: ## Run the app
	@GRAFANA_URL=$${GRAFANA_URL:-http://athena:3000} \
	$(UV) run -m book_club.__main__

test: ## Run tests (quiet)
	@PYTHONPATH=src $(UV) run -m pytest -q

coverage: ## Run tests with coverage
	@PYTHONPATH=src $(UV) run -m pytest --cov=src --cov-report=term-missing

lint: ## Lint (ruff)
	@$(UV) run ruff check .

fmt: ## Format (ruff)
	@$(UV) run ruff check --fix .
	@$(UV) run ruff format .

typecheck: ## Type-check (mypy)
	@$(UV) run mypy src

clean: ## Remove caches and build artifacts
	@rm -rf .venv .pytest_cache .mypy_cache dist build *.egg-info

dist: ## Build wheel/sdist (PEP 517; works if pyproject uses PEP 621)
	@$(UV) run -m pip install -U build
	@$(UV) run -m build

precommit: ## Run pre-commit on all files
	@$(UV) run pre-commit run --all-files

sync: ensure-uv ## Install app/runtime deps (from lockfile)
	@$(UV) sync

sync-dev: ensure-uv ## Install app + dev deps (from lockfile)
	@$(UV) sync --all-groups

push-tests: ## Push test metrics to Pushgateway (parallel execution with xdist)
	@$(UV) run pytest --pushgw=http://localhost:9091 --prom-job=pytest --prom-instance=dev --prom-tags=branch=main,run_id=local --prom-cleanup=none

verify-test-metrics: ## Verify complete test metrics pipeline (pytest → Pushgateway → Prometheus)
	@echo "🔍 Verifying test metrics pipeline..."
	@echo ""
	@echo "1️⃣  Running tests with metrics push..."
	@TEST_OUTPUT=$$($(UV) run pytest tests/observability/test_monitoring.py::test_server_health_endpoint \
		-p no:xdist -o addopts="" \
		--pushgw=http://localhost:9091 --prom-job=pytest_verify --prom-instance=verify \
		--prom-cleanup=none -q 2>&1); \
	if echo "$$TEST_OUTPUT" | grep -q "1 passed"; then \
		echo "✅ Test executed successfully"; \
	else \
		echo "❌ Test execution failed"; \
		echo "$$TEST_OUTPUT"; \
		exit 1; \
	fi
	@echo ""
	@echo "2️⃣  Checking metrics in Pushgateway..."
	@sleep 1
	@METRIC_COUNT=$$(curl -s http://localhost:9091/metrics | grep 'job="pytest_verify"' | grep "test_duration_seconds{" | wc -l); \
	if [ "$$METRIC_COUNT" -gt 0 ]; then \
		echo "✅ Found $$METRIC_COUNT metric(s) in Pushgateway"; \
		curl -s http://localhost:9091/metrics | grep 'job="pytest_verify"' | grep "test_duration_seconds{" | head -3; \
	else \
		echo "❌ No metrics found in Pushgateway for job=pytest_verify"; \
		exit 1; \
	fi
	@echo ""
	@echo "3️⃣  Checking Prometheus scrape target for Pushgateway..."
	@PROM_TARGET=$$(curl -s http://localhost:9090/api/v1/targets | \
		python3 -c "import sys, json; data=json.load(sys.stdin); \
		targets=[t for t in data['data']['activeTargets'] if 'pushgateway' in t.get('scrapePool','').lower() or 'pushgateway' in str(t.get('labels',{}))]; \
		print(targets[0]['health'] if targets else 'not_found')" 2>/dev/null || echo "error"); \
	if [ "$$PROM_TARGET" = "up" ]; then \
		echo "✅ Prometheus is scraping Pushgateway (status: up)"; \
	elif [ "$$PROM_TARGET" = "not_found" ]; then \
		echo "❌ Pushgateway target not found in Prometheus"; \
		exit 1; \
	else \
		echo "⚠️  Pushgateway target found but status: $$PROM_TARGET"; \
		exit 1; \
	fi
	@echo ""
	@echo "4️⃣  Verifying metrics reached Prometheus..."
	@sleep 2
	@PROM_METRICS=$$(curl -s "http://localhost:9090/api/v1/query?query=test_duration_seconds{job=\"pytest_verify\"}" | \
		python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('data',{}).get('result',[])))" 2>/dev/null || echo "0"); \
	if [ "$$PROM_METRICS" -gt 0 ]; then \
		echo "✅ Found $$PROM_METRICS metric(s) in Prometheus"; \
	else \
		echo "⚠️  Metrics not yet in Prometheus (may need to wait for scrape interval)"; \
	fi
	@echo ""
	@echo "5️⃣  Testing cleanup behavior..."
	@$(UV) run pytest tests/observability/test_pushgateway_cleanup.py::test_cleanup_before_prevents_accumulation -q
	@echo ""
	@echo "6️⃣  Cleaning up verification metrics..."
	@curl -s -X DELETE http://localhost:9091/metrics/job/pytest_verify >/dev/null 2>&1 || true
	@curl -s -X DELETE http://localhost:9091/metrics/job/pytest_cleanup_validation >/dev/null 2>&1 || true
	@echo "✅ Cleanup complete"
	@echo ""
	@echo "🎉 Test metrics pipeline verification complete!"
	@echo "   Pushgateway: http://localhost:9091"
	@echo "   Prometheus:  http://localhost:9090"
	@echo "   Grafana:     http://localhost:3000"

test-cleanup-behavior: ## Test all PROM_CLEANUP options (none, before, after, both)
	@echo "🧪 Testing Pushgateway cleanup behavior..."
	@echo "   (Running sequentially to avoid race conditions)"
	@$(UV) run pytest tests/observability/test_pushgateway_cleanup.py -p no:xdist -o addopts="" -v

# -------- Docker Compose v2 (installer) --------
# To override the version at invocation time: make compose-install COMPOSE_VERSION=v2.30.3
COMPOSE_VERSION ?= v2.29.2

compose-install: ## Install Docker Compose v2 (Docker APT repo on Ubuntu or user-space fallback)
	@set -e; \
	if docker compose version >/dev/null 2>&1; then echo "✅ Docker Compose v2 already installed"; exit 0; fi; \
	if command -v apt >/dev/null 2>&1; then \
	  echo "➤ Installing Docker Compose v2 via Docker's APT repository..."; \
	  sudo apt update; \
	  sudo apt install -y ca-certificates curl gnupg; \
	  sudo install -m 0755 -d /etc/apt/keyrings; \
	  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg; \
	  sudo chmod a+r /etc/apt/keyrings/docker.gpg; \
	  . /etc/os-release; \
	  echo "deb [arch=$$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $$UBUNTU_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null; \
	  sudo apt update; \
	  sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || sudo apt install -y docker-compose-plugin; \
	else \
	  echo "➤ Installing Compose v2 as a CLI plugin in user space..."; \
	  mkdir -p $$HOME/.docker/cli-plugins; \
	  arch=$$(uname -m); \
	  case $$arch in \
	    x86_64) bin=docker-compose-linux-x86_64 ;; \
	    aarch64|arm64) bin=docker-compose-linux-aarch64 ;; \
	    *) echo "Unsupported architecture: $$arch"; exit 1 ;; \
	  esac; \
	  curl -SL "https://github.com/docker/compose/releases/download/$(COMPOSE_VERSION)/$$bin" -o $$HOME/.docker/cli-plugins/docker-compose; \
	  chmod +x $$HOME/.docker/cli-plugins/docker-compose; \
	fi; \
	docker compose version

compose-version: ## Show Docker Compose v2 version if installed
	@docker compose version || true

compose-switch: ## Optional: install docker-compose-switch to map docker-compose -> docker compose
	@sudo apt install -y docker-compose-switch || true

# -------- Observability Stack Verification --------

verify-observability: ## Verify complete observability pipeline (Alloy → Loki → Grafana)
	@echo "🔍 Verifying observability stack..."
	@echo ""
	@echo "1  Checking services are running..."
	@docker compose ps alloy loki grafana prometheus | grep -E "(Up|running)" > /dev/null || (echo "❌ Services not running. Run: docker compose up -d" && exit 1)
	@echo "✅ All services running"
	@echo ""
	@echo "2  Checking health endpoints..."
	@curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready > /dev/null || (echo "❌ Loki not ready" && exit 1)
	@echo "✅ Loki ready"
	@curl -sf http://localhost:3000/api/health > /dev/null || (echo "❌ Grafana not healthy" && exit 1)
	@echo "✅ Grafana healthy"
	@curl -sf http://localhost:12345/ > /dev/null || (echo "❌ Alloy not responding" && exit 1)
	@echo "✅ Alloy responding"
	@echo ""
	@echo "3  Generating test log..."
	@$(PY) main.py
	@echo "✅ Test log generated"
	@echo ""
	@echo "4  Waiting 3 seconds for ingestion..."
	@sleep 3
	@echo ""
	@echo "5  Querying Loki for logs..."
	@LOG_COUNT=$$(curl -s -H "X-Scope-OrgID: local" "http://localhost:3100/loki/api/v1/labels" | grep -o "filename" | wc -l); \
	if [ "$$LOG_COUNT" -eq 0 ]; then \
		echo "❌ No logs found in Loki"; \
		exit 1; \
	fi
	@echo "✅ Logs present in Loki (labels found)"
	@echo ""
	@echo "6 Checking Grafana datasources..."
	@DATASOURCE_OK=$$(curl -s http://localhost:3000/api/datasources | grep -o "http://loki:3100" | wc -l); \
	if [ "$$DATASOURCE_OK" -eq 0 ]; then \
		echo "❌ Loki datasource not configured in Grafana"; \
		exit 1; 
	fi
	@echo "✅ Grafana datasources configured"
	@echo ""
	@echo "🎉 Observability stack verification complete!"
	@echo "   View logs at: http://localhost:3000/explore"

verify-quick: ## Quick check: services up and Loki accessible
	@docker compose ps alloy loki grafana | grep -E "(Up|running)" > /dev/null && echo "✅ Services running" || echo "❌ Services down"
	@curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready > /dev/null && echo "✅ Loki ready" || echo "❌ Loki not ready"
	@curl -sf http://localhost:3000/api/health > /dev/null && echo "✅ Grafana healthy" || echo "❌ Grafana down"

verify-logs: ## Check if recent logs reached Loki
	@echo "📊 Checking recent logs in Loki..."
	@END=$$(date +%s)000000000; \
	START=$$(($$END - 600000000000)); \
	RESULT=$$(curl -s -H "X-Scope-OrgID: local" "http://localhost:3100/loki/api/v1/query_range" \
		--data-urlencode 'query={filename="main.py"}' \
		--data-urlencode "start=$$START" \
		--data-urlencode "end=$$END"); \
	if echo "$$RESULT" | grep -q '"result":\[\]'; then \
		echo "❌ No logs from main.py found in last 10 minutes"; \
		exit 1; \
	else \
		echo "✅ Logs found in Loki"; \
		echo "$$RESULT" | grep -o '"stream":{[^}]*}' | head -3; \
	fi

verify-integration: ## End-to-end: app+server+observability
	@echo "➡ Bringing up stack..."
	@docker compose up -d
	@echo "➡ Waiting for server..."
	@until curl -sf http://localhost:8010/health >/dev/null; do sleep 1; done
	@echo "✅ Server healthy"
	@echo "➡ Waiting for app..."
	@until curl -sf http://localhost:8000/ >/dev/null; do sleep 1; done
	@echo "✅ App reachable"
	@echo "➡ In-cluster: app -> server health"
	@docker compose exec -T bookclub-app wget -qO- http://bookclub-server:8010/health | grep -q '"status": "ok"' && echo "✅ App can reach server"
	@echo "➡ Metrics endpoint"
	@curl -sf http://localhost:8010/metrics | head -n 5 >/dev/null && echo "✅ /metrics served"
	@echo "➡ Prometheus targets"
	@curl -sf http://localhost:9090/api/v1/targets | jq -e '.data.activeTargets[] | select(.labels.job=="bookclub-server" and .health=="up")' >/dev/null && echo "✅ Prometheus scraping bookclub-server" || (echo "❌ Prometheus target down"; exit 1)
	@echo "➡ Loki ready"
	@curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready >/dev/null && echo "✅ Loki ready"
	@echo "➡ Grafana health"
	@curl -sf http://localhost:3000/api/health >/dev/null && echo "✅ Grafana healthy"
	@echo "🎉 Integration OK"

purge-old-data: ## Clean all observability data (logs, metrics, traces) but keep configs/dashboards
	@echo "🧹 Purging old observability data..."
	@echo ""
	@echo "⚠️  This will delete:"
	@echo "   • All log files"
	@echo "   • All Prometheus metrics history"
	@echo "   • All Loki log history"
	@echo "   • All Pushgateway metrics"
	@echo "   • All Qdrant vector data"
	@echo "   • Grafana session data"
	@echo ""
	@echo "✅ This will keep:"
	@echo "   • All configuration files"
	@echo "   • All Grafana dashboards"
	@echo "   • All datasource definitions"
	@echo ""
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		echo "1️⃣  Stopping services..."; \
		docker compose stop prometheus loki pushgateway qdrant grafana alloy || true; \
		echo ""; \
		echo "2️⃣  Cleaning log files..."; \
		rm -rf logs/*.log && echo "   ✅ Cleaned logs/"; \
		rm -rf src/book_club/app/logs/*.log && echo "   ✅ Cleaned app logs/" || true; \
		rm -rf src/book_club/server/logs/*.log && echo "   ✅ Cleaned server logs/" || true; \
		echo ""; \
		echo "3️⃣  Cleaning Prometheus data..."; \
		rm -rf observability/prometheus/data/* && echo "   ✅ Cleaned Prometheus data"; \
		echo ""; \
		echo "4️⃣  Cleaning Loki data..."; \
		rm -rf observability/loki/data/* && echo "   ✅ Cleaned Loki data"; \
		echo ""; \
		echo "5️⃣  Cleaning Qdrant data..."; \
		rm -rf data/qdrant/* && echo "   ✅ Cleaned Qdrant data"; \
		echo ""; \
		echo "6️⃣  Cleaning Grafana session data..."; \
		rm -rf observability/grafana/data/grafana.db* && echo "   ✅ Cleaned Grafana sessions" || true; \
		echo ""; \
		echo "7️⃣  Restarting services..."; \
		docker compose up -d prometheus loki pushgateway qdrant grafana alloy; \
		echo ""; \
		echo "8️⃣  Waiting for services to be ready..."; \
		sleep 5; \
		echo ""; \
		echo "9️⃣  Verifying clean state..."; \
		curl -sf http://localhost:9090/api/v1/query?query=up >/dev/null && echo "   ✅ Prometheus running"; \
		curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready >/dev/null && echo "   ✅ Loki running"; \
		curl -sf http://localhost:9091/metrics >/dev/null && echo "   ✅ Pushgateway running"; \
		curl -sf http://localhost:3000/api/health >/dev/null && echo "   ✅ Grafana running"; \
		echo ""; \
		echo "🎉 Observability data purged successfully!"; \
		echo ""; \
		echo "📊 Access points:"; \
		echo "   • Grafana:     http://localhost:3000"; \
		echo "   • Prometheus:  http://localhost:9090"; \
		echo "   • Loki:        http://localhost:3100"; \
		echo "   • Pushgateway: http://localhost:9091"; \
	else \
		echo ""; \
		echo "❌ Purge cancelled"; \
	fi