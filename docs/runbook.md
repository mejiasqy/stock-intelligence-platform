# Runbook — Stock Intelligence Platform

Guia operacional para configurar, executar e validar o projeto localmente.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Instalação |
|---|---|---|
| Python | 3.12 | python.org |
| uv | 0.11+ | `pip install uv` ou `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | nodejs.org |
| Docker | 24+ | docker.com |
| Docker Compose | v2+ | incluído no Docker Desktop |

---

## Setup inicial

```bash
# 1. Clone
git clone https://github.com/mejiasqy/stock-intelligence-platform.git
cd stock-intelligence-platform

# 2. Copie variáveis de ambiente
cp .env.example .env
# Edite .env — mínimo obrigatório: DATABASE_URL

# 3. Instale dependências
make setup

# 4. Suba banco
docker compose up -d db

# 5. Aguarde banco estar healthy
docker compose ps  # STATUS: healthy

# 6. Execute migrations (Sprint 1+)
make migrate
```

---

## Executar localmente

### Backend

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Acesse:
- API: http://localhost:8000/api/v1/health
- Docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

Acesse: http://localhost:3000

---

## Comandos de validação

```bash
make test        # testes backend
make lint        # ruff + eslint
make format      # aplicar formatação
make typecheck   # mypy + tsc
make verify      # verificar ambiente
```

---

## Parar serviços

```bash
docker compose down        # para o banco
docker compose down -v     # para o banco E remove dados (cuidado)
```

---

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Backend não inicia | `.env` ausente | `cp .env.example .env` |
| Banco recusa conexão | Docker não rodando | `docker compose up -d db` |
| `uv sync` falha | Python < 3.12 | Instalar Python 3.12+ |
| `npm install` falha | Node < 18 | Instalar Node 18+ |
| Port 5432 em uso | Outro PostgreSQL rodando | Alterar porta no `docker-compose.yml` |
