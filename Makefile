.PHONY: help setup dev test lint format typecheck migrate seed verify

help: ## Exibe os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Instala dependências do backend e frontend
	cd backend && uv sync
	cd frontend && npm install

dev: ## Sobe banco e inicia backend e frontend em modo desenvolvimento
	docker compose up -d db
	@echo "Banco iniciado. Inicie backend e frontend manualmente:"
	@echo "  Backend:  cd backend && uv run uvicorn app.main:app --reload --port 8000"
	@echo "  Frontend: cd frontend && npm run dev"

test: ## Executa testes do backend
	cd backend && uv run pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Verifica lint no backend (ruff) e frontend (eslint)
	cd backend && uv run ruff check .
	cd frontend && npm run lint

format: ## Aplica formatação no backend (ruff format)
	cd backend && uv run ruff format .

format-check: ## Verifica formatação sem alterar arquivos
	cd backend && uv run ruff format --check .

typecheck: ## Verifica tipos no backend (mypy) e frontend (tsc)
	cd backend && uv run mypy app/
	cd frontend && npx tsc --noEmit

migrate: ## Executa migrations pendentes
	cd backend && uv run alembic upgrade head

seed: ## Popula banco com dados de demonstração
	cd backend && uv run python -m scripts.seed_demo_data

verify: ## Verifica pré-requisitos do ambiente
	python scripts/verify_environment.py
