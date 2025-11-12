# ===== Book Club POC — uv-driven Makefile =====

SHELL := /bin/bash

# Colors
define colour_fns
blue()   { printf '\033[0;34m%s\033[0m\n' "$$1"; }
green()  { printf '\033[0;32m%s\033[0m\n' "$$1"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$$1"; }
red()    { printf '\033[0;31m%s\033[0m\n' "$$1"; }
endef
export colour_fns


.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-builtin-rules
.DEFAULT_GOAL := help

UV := $(HOME)/.local/bin/uv
PY := .venv/bin/python
PIP := .venv/bin/pip


# -------- Targets --------

help: ## Show this help
	@$(colour_fns)
	@echo ""
	@blue "════════════════════════════════════════════════════════════════════════════════"
	@echo "  Book Club POC — Make Targets"
	@blue "════════════════════════════════════════════════════════════════════════════════"
	@echo ""
	@blue "SETUP & ENVIRONMENT"
	@grep -E '^(ensure-uv|venv|deps-seed|lock|install|install-dev|setup|sync|sync-dev):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "DEVELOPMENT"
	@grep -E '^(run|test|coverage|lint|fmt|typecheck|precommit):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "BUILD & CLEAN"
	@grep -E '^(clean|dist):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "TESTING & METRICS"
	@grep -E '^(push-tests|verify-test-metrics|test-cleanup-behavior):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "DOCKER COMPOSE"
	@grep -E '^(compose-install|compose-version|compose-switch):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "OBSERVABILITY VERIFICATION"
	@grep -E '^(verify-observability|verify-quick|verify-logs|verify-integration):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "OBSERVABILITY UI ACCESS"
	@grep -E '^(open-observability-firefox|open-observability-chrome):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "MAINTENANCE"
	@grep -E '^(purge-old-data):.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@blue "════════════════════════════════════════════════════════════════════════════════"
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
	@echo "uv environment ready."

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
	@$(colour_fns)
	@blue "Verifying test metrics pipeline..."
	@echo ""
	@blue "1. Running tests with metrics push..."
	@TEST_OUTPUT=$$($(UV) run pytest tests/observability/test_monitoring.py::test_server_health_endpoint \
		-p no:xdist -o addopts="" \
		--pushgw=http://localhost:9091 --prom-job=pytest_verify --prom-instance=verify \
		--prom-cleanup=none -q 2>&1); \
	if echo "$$TEST_OUTPUT" | grep -q "1 passed"; then \
		green "Test executed successfully"; \
	else \
		red "Test execution failed"; \
		echo "$$TEST_OUTPUT"; \
		exit 1; \
	fi
	@echo ""
	@blue "2. Checking metrics in Pushgateway..."
	@sleep 1
	@METRIC_COUNT=$$(curl -s http://localhost:9091/metrics | grep 'job="pytest_verify"' | grep "test_duration_seconds{" | wc -l); \
	if [ "$$METRIC_COUNT" -gt 0 ]; then \
		green "Found $$METRIC_COUNT metric(s) in Pushgateway"; \
		curl -s http://localhost:9091/metrics | grep 'job="pytest_verify"' | grep "test_duration_seconds{" | head -3; \
	else \
		red "No metrics found in Pushgateway for job=pytest_verify"; \
		exit 1; \
	fi
	@echo ""
	@blue "3. Checking Prometheus scrape target for Pushgateway..."
	@PROM_TARGET=$$(curl -s http://localhost:9090/api/v1/targets | \
		python3 -c "import sys, json; data=json.load(sys.stdin); \
		targets=[t for t in data['data']['activeTargets'] if 'pushgateway' in t.get('scrapePool','').lower() or 'pushgateway' in str(t.get('labels',{}))]; \
		print(targets[0]['health'] if targets else 'not_found')" 2>/dev/null || echo "error"); \
	if [ "$$PROM_TARGET" = "up" ]; then \
		green "Prometheus is scraping Pushgateway (status: up)"; \
	elif [ "$$PROM_TARGET" = "not_found" ]; then \
		red "Pushgateway target not found in Prometheus"; \
		exit 1; \
	else \
		red "Pushgateway target found but status: $$PROM_TARGET"; \
		exit 1; \
	fi
	@echo ""
	@blue "4. Verifying metrics reached Prometheus..."
	@sleep 2
	@PROM_METRICS=$$(curl -s "http://localhost:9090/api/v1/query?query=test_duration_seconds{job=\"pytest_verify\"}" | \
		python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('data',{}).get('result',[])))" 2>/dev/null || echo "0"); \
	if [ "$$PROM_METRICS" -gt 0 ]; then \
		green "Found $$PROM_METRICS metric(s) in Prometheus"; \
	else \
		yellow "Metrics not yet in Prometheus (may need to wait for scrape interval)"; \
	fi
	@echo ""
	@blue "5. Testing cleanup behaviour..."
	@$(UV) run pytest tests/observability/test_pushgateway_cleanup.py::test_cleanup_before_prevents_accumulation -q
	@echo ""
	@blue "6. Cleaning up verification metrics..."
	@curl -s -X DELETE http://localhost:9091/metrics/job/pytest_verify >/dev/null 2>&1 || true
	@curl -s -X DELETE http://localhost:9091/metrics/job/pytest_cleanup_validation >/dev/null 2>&1 || true
	@green "Cleanup complete"
	@echo ""
	@green "Test metrics pipeline verification complete!"
	@echo "   Pushgateway: http://localhost:9091"
	@echo "   Prometheus:  http://localhost:9090"
	@echo "   Grafana:     http://localhost:3000"

test-cleanup-behavior: ## Test all PROM_CLEANUP options (none, before, after, both)
	@$(colour_fns)
	@blue "Testing Pushgateway cleanup behaviour..."
	@echo ""
	@$(UV) run pytest tests/observability/test_pushgateway_cleanup.py -p no:xdist -o addopts="" -v

# -------- Docker Compose v2 (installer) --------
# To override the version at invocation time: make compose-install COMPOSE_VERSION=v2.30.3
COMPOSE_VERSION ?= v2.29.2

compose-install: ## Install Docker Compose v2 (Docker APT repo on Ubuntu or user-space fallback)
	@set -e; \
	if docker compose version >/dev/null 2>&1; then echo "Docker Compose v2 already installed"; exit 0; fi; \
	if command -v apt >/dev/null 2>&1; then \
	  echo "Installing Docker Compose v2 via Docker's APT repository..."; \
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
	  echo "Installing Compose v2 as a CLI plugin in user space..."; \
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
	@$(colour_fns)
	@blue "Verifying observability stack..."
	@echo ""
	@blue "1. Checking services are running..."
	@docker compose ps alloy loki grafana prometheus | grep -E "(Up|running)" > /dev/null || (red "Services not running. Run: docker compose up -d" && exit 1)
	@green "All services running"
	@echo ""
	@blue "2. Checking health endpoints..."
	@curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready > /dev/null || (red "Loki not ready" && exit 1)
	@green "Loki ready"
	@curl -sf http://localhost:3000/api/health > /dev/null || (red "Grafana not healthy" && exit 1)
	@green "Grafana healthy"
	@curl -sf http://localhost:12345/ > /dev/null || (red "Alloy not responding" && exit 1)
	@green "Alloy responding"
	@echo ""
	@blue "3. Generating test log..."
	@$(PY) main.py
	@green "Test log generated"
	@echo ""
	@blue "4. Waiting 3 seconds for ingestion..."
	@sleep 3
	@echo ""
	@blue "5. Querying Loki for logs..."
	@LOG_COUNT=$$(curl -s -H "X-Scope-OrgID: local" "http://localhost:3100/loki/api/v1/labels" | grep -o "filename" | wc -l); \
	if [ "$$LOG_COUNT" -eq 0 ]; then \
		red "No logs found in Loki"; \
		exit 1; \
	fi
	@green "Logs present in Loki (labels found)"
	@echo ""
	@blue "6  Checking Grafana datasources..."
	@DATASOURCE_OK=$$(curl -s http://localhost:3000/api/datasources | grep -o "http://loki:3100" | wc -l); \
	if [ "$$DATASOURCE_OK" -eq 0 ]; then \
		red "Loki datasource not configured in Grafana"; \
		exit 1;
	fi
	@green "Grafana datasources configured"
	@echo ""
	@green "Observability stack verification complete!"
	@blue "View logs at: http://localhost:3000/explore"

verify-quick: ## Quick check: services up and Loki accessible
	@$(colour_fns)
	@docker compose ps alloy loki grafana | grep -E "(Up|running)" > /dev/null && green "Services running" || red "Services down"
	@curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready > /dev/null && green "Loki ready" || red "Loki not ready"
	@curl -sf http://localhost:3000/api/health > /dev/null && green "Grafana healthy" || red "Grafana down"


verify-logs: ## Check if recent logs reached Loki
	@$(colour_fns)
	@blue "Checking recent logs in Loki..."
	@END=$$(date +%s)000000000; \
	START=$$(($$END - 600000000000)); \
	RESULT=$$(curl -s -H "X-Scope-OrgID: local" "http://localhost:3100/loki/api/v1/query_range" \
		--data-urlencode 'query={filename="main.py"}' \
		--data-urlencode "start=$$START" \
		--data-urlencode "end=$$END"); \
	if echo "$$RESULT" | grep -q '"result":\[\]'; then \
		red "No logs from main.py found in last 10 minutes"; \
		exit 1; \
	else \
		green "Logs found in Loki"; \
		echo "$$RESULT" | grep -o '"stream":{[^}]*}' | head -3; \
	fi

verify-integration: ## End-to-end: app+server+observability
	@$(colour_fns)
	@blue "Bringing up stack..."
	@docker compose up -d
	@blue "Waiting for server..."
	@until curl -sf http://localhost:8010/health >/dev/null; do sleep 1; done
	@green "Server healthy"
	@blue "Waiting for app..."
	@until curl -sf http://localhost:8000/ >/dev/null; do sleep 1; done
	@green "App reachable"
	@blue "In-cluster: app -> server health"
	@docker compose exec -T bookclub-app wget -qO- http://bookclub-server:8010/health | grep -q '"status":"ok"' && green "App can reach server" || red "App could not reach server"
	@blue "Metrics endpoint"
	@curl -sf http://localhost:8010/metrics | head -n 5 >/dev/null && green "/metrics served" || red "Metrics endpoint not available"
	@blue "Prometheus targets"
	@curl -sf http://localhost:9090/api/v1/targets | jq -e '.data.activeTargets[] | select(.labels.job=="bookclub-server" and .health=="up")' >/dev/null && green "Prometheus scraping bookclub-server" || (red "Prometheus target down"; exit 1)
	@blue "Loki readiness"
	@curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready >/dev/null && green "Loki ready" || red "Loki not ready"
	@blue "Grafana health"
	@curl -sf http://localhost:3000/api/health >/dev/null && green "Grafana healthy" || red "Grafana down"
	@green "Integration OK"

open-observability-firefox: ## Open observability dashboards in Firefox
	@powershell.exe -NoLogo -NoProfile -Command '\
	  $$urls = @("http://localhost:8000/","http://localhost:3000","http://localhost:9090","http://localhost:3100","http://localhost:9091"); \
	  $$proc = Get-Process firefox -ErrorAction SilentlyContinue | Select-Object -First 1; \
	  $$firefox = $$null; \
	  if ($$proc) { $$firefox = $$proc.Path; } \
	  if (-not $$firefox) { $$firefox = (Get-Command firefox.exe -ErrorAction SilentlyContinue).Source; } \
	  if (-not $$firefox -and (Test-Path "C:\Program Files\Mozilla Firefox\firefox.exe")) { $$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"; } \
	  if (-not $$firefox -and (Test-Path "C:\Program Files (x86)\Mozilla Firefox\firefox.exe")) { $$firefox = "C:\Program Files (x86)\Mozilla Firefox\firefox.exe"; } \
	  if (-not $$firefox) { Write-Error "Firefox not found via process scan or standard install paths."; exit 1; } \
	  Start-Process -FilePath $$firefox -ArgumentList ($$urls | ForEach-Object { "-new-tab", $$_ });' >/dev/null 2>&1
	@printf 'Requested Firefox to open Grafana, Prometheus, Loki, and Pushgateway.\n'

open-observability-chrome: ## Open observability dashboards in Google Chrome
	@powershell.exe -NoLogo -NoProfile -Command '\
	  $$urls = @("http://localhost:3000","http://localhost:9090","http://localhost:3100","http://localhost:9091"); \
	  $$proc = Get-Process chrome -ErrorAction SilentlyContinue | Select-Object -First 1; \
	  $$chrome = $$null; \
	  if ($$proc) { $$chrome = $$proc.Path; } \
	  if (-not $$chrome) { $$chrome = (Get-Command chrome.exe -ErrorAction SilentlyContinue).Source; } \
	  if (-not $$chrome -and (Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe")) { $$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"; } \
	  if (-not $$chrome -and (Test-Path "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")) { $$chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"; } \
	  if (-not $$chrome) { Write-Error "Google Chrome not found via process scan or standard install paths."; exit 1; } \
	  Start-Process -FilePath $$chrome -ArgumentList ($$urls | ForEach-Object { "--new-tab", $$_ });' >/dev/null 2>&1
	@printf 'Requested Google Chrome to open Grafana, Prometheus, Loki, and Pushgateway.\n'

purge-old-data: ## Clean all observability data (logs, metrics, traces) but keep configs/dashboards
	@$(colour_fns)
	@blue "Purging old observability data..."
	@echo ""
	@yellow "This will be deleted:"
	@yellow "   • All log files"
	@yellow "   • All Prometheus metrics history"
	@yellow "   • All Loki log history"
	@yellow "   • All Pushgateway metrics"
	@yellow "   • All Qdrant vector data"
	@yellow "   • Grafana session data"
	@echo ""
	@blue "This will be kept:"
	@blue "   • All configuration files"
	@blue "   • All Grafana dashboards"
	@blue "   • All datasource definitions"
	@echo ""
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		blue "1. Stopping services..."; \
		docker compose stop prometheus loki pushgateway qdrant grafana alloy || true; \
		echo ""; \
		blue "2. Cleaning log files..."; \
		rm -rf logs/*.log && green "Cleaned logs/"; \
		rm -rf src/book_club/app/logs/*.log && green "Cleaned app logs/" || true; \
		rm -rf src/book_club/server/logs/*.log && green "Cleaned server logs/" || true; \
		echo ""; \
		blue "3. Cleaning Prometheus data..."; \
		rm -rf observability/prometheus/data/* && green "Cleaned Prometheus data"; \
		echo ""; \
		blue "4. Cleaning Loki data..."; \
		rm -rf observability/loki/data/* && green "Cleaned Loki data"; \
		echo ""; \
		blue "5. Cleaning Qdrant data..."; \
		rm -rf data/qdrant/* && green "Cleaned Qdrant data"; \
		echo ""; \
		blue "6. Cleaning Grafana session data..."; \
		rm -rf observability/grafana/data/grafana.db* && green "Cleaned Grafana sessions" || true; \
		echo ""; \
		blue "7. Restarting services..."; \
		docker compose up -d prometheus loki pushgateway qdrant grafana alloy; \
		echo ""; \
		blue "8. Waiting for services to be ready..."; \
		sleep 5; \
		echo ""; \
		blue "9. Verifying clean state..."; \
		curl -sf http://localhost:9090/api/v1/query?query=up >/dev/null && green "Prometheus running" || red "Prometheus down"; \
		curl -sf -H "X-Scope-OrgID: local" http://localhost:3100/ready >/dev/null && green "Loki running" || red "Loki down"; \
		curl -sf http://localhost:9091/metrics >/dev/null && green "Pushgateway running" || red "Pushgateway down"; \
		curl -sf http://localhost:3000/api/health >/dev/null && green "Grafana running" || red "Grafana down"; \
		echo ""; \
		green "Observability data purged successfully!"; \
		echo ""; \
		blue "Access points:"; \
		blue "   • Grafana:     http://localhost:3000"; \
		blue "   • Prometheus:  http://localhost:9090"; \
		blue "   • Loki:        http://localhost:3100"; \
		blue "   • Pushgateway: http://localhost:9091"; \
	else \
		echo ""; \
		yellow "Purge cancelled"; \
	fi
