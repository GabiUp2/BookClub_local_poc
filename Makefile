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
	@grep -E '^[a-zA-Z0-9_\-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*##/: /' | column -s': ' -t

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
	httpx>=0.27.0
	pydantic>=2.8.0
	rich>=13.7.0
	REQ
	@[ -f requirements-dev.in ] || cat > requirements-dev.in <<-'REQ'
	pytest>=8.2.0
	pytest-cov>=5.0.0
	ruff>=0.6.0
	mypy>=1.11.0
	pre-commit>=3.7.0
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

# -------- Docker Compose v2 (installer) --------
# You can override the version at invocation time: make compose-install COMPOSE_VERSION=v2.30.3
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