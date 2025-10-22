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
	@$(PIP) install -U pip wheel

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
	@$(UV) pip compile requirements.in -o requirements.lock
	@$(UV) pip compile requirements-dev.in -o requirements-dev.lock -c requirements.lock

install: venv lock ## Install from lockfiles into .venv
	@$(PIP) install -r requirements.lock -r requirements-dev.lock
	@.venv/bin/pre-commit install || true

setup: install ## Full setup (uv + venv + locked deps)
	@echo "✅ uv environment ready."

run: ## Run the app
	@GRAFANA_URL=$${GRAFANA_URL:-http://athena:3000} \
	$(PY) -m book_club.__main__

test: ## Run tests (quiet)
	@PYTHONPATH=src $(PY) -m pytest -q

coverage: ## Run tests with coverage
	@PYTHONPATH=src $(PY) -m pytest --cov=src --cov-report=term-missing

lint: ## Lint (ruff)
	@.venv/bin/ruff check .

fmt: ## Format (ruff)
	@.venv/bin/ruff check --fix .
	@.venv/bin/ruff format .

typecheck: ## Type-check (mypy)
	@.venv/bin/mypy src

clean: ## Remove caches and build artifacts
	@rm -rf .venv .pytest_cache .mypy_cache dist build *.egg-info

dist: ## Build wheel/sdist (PEP 517; works if pyproject uses PEP 621)
	@$(PIP) install -U build
	@$(PY) -m build

precommit: ## Run pre-commit on all files
	@.venv/bin/pre-commit run --all-files
