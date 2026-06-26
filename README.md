# Stock Intelligence Platform

Plataforma de análise de ações, monitoramento de mercado, ranking de ativos, backtesting de estratégias e geração de relatórios assistidos por IA.

> **Aviso:** este sistema é educacional e analítico. Não executa ordens de compra/venda, não garante rentabilidade e não constitui recomendação financeira. Todo sinal produzido é um **instrumento analítico baseado em dados históricos**.

---

## Funcionalidades (MVP)

- Coleta e armazenamento de dados históricos de ativos (OHLCV)
- Cálculo de indicadores técnicos: SMA, EMA, RSI, MACD, Bandas de Bollinger
- Ranking de ativos por score configurável e transparente
- Sinais analíticos explicáveis com reason codes
- Backtesting de estratégias com auditabilidade completa
- Dashboard interativo com gráficos e detalhe de ativo
- Relatórios analíticos assistidos por IA com fallback determinístico
- Alertas informativos (Telegram ou e-mail)

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.14, FastAPI, SQLAlchemy 2, Alembic, pandas, numpy |
| Banco | PostgreSQL 16 |
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, TanStack Query v5, Recharts |
| Testes | pytest (backend) · Vitest + React Testing Library (frontend) |
| Infra | Docker Compose, GitHub Actions |
| Qualidade | Ruff, mypy, ESLint, TypeScript strict |

---

## Como executar localmente

### Pré-requisitos

- Python 3.12+
- Node.js 18+
- Docker e Docker Compose
- [uv](https://docs.astral.sh/uv/) — gerenciador de pacotes Python

### Setup completo

```bash
# 1. Clone o repositório
git clone https://github.com/mejiasqy/stock-intelligence-platform.git
cd stock-intelligence-platform

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env conforme necessário

# 3. Instale todas as dependências
make setup

# 4. Suba o banco de dados
docker compose up -d db

# 5. Execute as migrations (Sprint 1+)
make migrate

# 6. Inicie o backend (porta 8000)
cd backend && uv run uvicorn app.main:app --reload --port 8000

# 7. Em outro terminal, inicie o frontend (porta 3000)
cd frontend && npm run dev
```

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Documentação OpenAPI | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |

---

## Comandos úteis

```bash
make setup      # Instala dependências (backend + frontend)
make test       # Executa testes do backend
make lint       # Verifica lint (ruff + eslint)
make format     # Aplica formatação (ruff format)
make typecheck  # Verifica tipos (mypy + tsc)
make migrate    # Executa migrations (alembic upgrade head)
make verify     # Verifica pré-requisitos do ambiente
```

---

## Dashboard (Sprint 6)

O dashboard consome exclusivamente endpoints de leitura da API — nenhuma chave administrativa é enviada ou exposta pelo browser.

| Página | URL | O que mostra |
|---|---|---|
| Overview | `/` | KPIs: total de ativos, contagem bullish/bearish, status da API; ranking top 10 por score |
| Watchlist | `/watchlist` | Tabela de todos os sinais com filtros (alta/baixa/neutro/insuficiente) |
| Detalhe do ativo | `/assets/{symbol}` | Gráfico de fechamento histórico, indicadores técnicos pontuais, composição do score, reason_codes |
| Backtests | `/backtests` | Lista de execuções com curva de patrimônio, métricas, parâmetros e trades simulados |

Todos os estados implementados: **carregando**, **vazio**, **erro** (com `request_id` discreto), **insufficient_data** e **sucesso**.

### Screenshots reais (dados de demonstração)

| Tela | Preview |
|---|---|
| Overview | `docs/screenshots/01-overview.png` |
| Watchlist | `docs/screenshots/02-watchlist-all.png` |
| Watchlist filtrada (bullish) | `docs/screenshots/03-watchlist-bullish.png` |
| Detalhe ITUB4.SA (bullish, score 62) | `docs/screenshots/05-asset-detail-itub4.png` |
| Detalhe MGLU3.SA (bearish, score 15) | `docs/screenshots/06-asset-detail-mglu3.png` |
| Estado de erro (ativo não encontrado) | `docs/screenshots/07-asset-detail-error.png` |
| Backtests — lista | `docs/screenshots/08-backtests-list.png` |
| Backtests — PETR4.SA expandido | `docs/screenshots/09-backtests-detail.png` |

Consulte [`docs/screenshots/README.md`](docs/screenshots/README.md) para detalhes de captura e limitações conhecidas.

---

## Testes

```bash
# Backend (222 testes: unit + integração com banco real)
cd backend && uv run pytest tests/ -v

# Frontend (35 testes Vitest: componentes, API layer, contratos)
cd frontend && npm test

# Lint e typecheck
cd backend && uv run ruff check . && uv run mypy app/
cd frontend && npm run lint && npx tsc --noEmit
```

---

## Variáveis de ambiente

Consulte `.env.example` para a lista completa. As variáveis obrigatórias para desenvolvimento são:

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql://...` | URL do PostgreSQL |
| `API_SECRET_KEY` | `change-me-in-production` | Chave dos endpoints administrativos (`X-Api-Key`) |
| `ENVIRONMENT` | `development` | Ambiente de execução |
| `CORS_ORIGINS` | `http://localhost:3000` | Origins permitidas (separadas por vírgula) |
| `CORS_METHODS` | `GET,POST,OPTIONS` | Métodos HTTP permitidos pelo CORS |
| `CORS_ALLOW_HEADERS` | `Content-Type,X-Api-Key,X-Request-ID` | Headers permitidos pelo CORS |
| `PAGINATION_DEFAULT_LIMIT` | `50` | Itens por página padrão |
| `PAGINATION_MAX_LIMIT` | `100` | Máximo geral de itens por página |
| `PAGINATION_MAX_LIMIT_TRADES` | `500` | Máximo de trades por página |
| `RATE_LIMIT_DEFAULT` | `120/minute` | Rate limit geral por IP |
| `RATE_LIMIT_BACKTESTS` | `10/minute` | Rate limit para execução de backtests |
| `LLM_PROVIDER` | `anthropic` | Provider de IA (suporta `anthropic`) |
| `LLM_MODEL` | `claude-haiku-4-5-20251001` | Modelo LLM para relatórios analíticos |
| `LLM_API_KEY` | *(vazio)* | Chave do provider LLM — nunca versionar com valor real |
| `LLM_TIMEOUT_SECONDS` | `30` | Timeout da chamada ao LLM em segundos |
| `ALERTS_ENABLED` | `false` | Habilita envio de alertas (opt-in) |
| `ALERTS_DRY_RUN` | `true` | Registra payload sem enviar ao Telegram |
| `TELEGRAM_BOT_TOKEN` | *(vazio)* | Token do bot Telegram — nunca versionar com valor real |
| `TELEGRAM_CHAT_ID` | *(vazio)* | Chat ID do Telegram — nunca versionar com valor real |
| `ALERT_DEDUP_HOURS` | `24` | Janela de deduplicação de alertas em horas |
| `SCHEDULER_ENABLED` | `false` | Habilita job diário automático (opt-in) |
| `DAILY_JOB_TIME` | `18:00` | Horário do job diário (não representa calendário de pregão) |

---

## Arquitetura

Consulte [`docs/architecture.md`](docs/architecture.md) para o diagrama e decisões técnicas.

---

## Limitações e disclaimer

- Performance passada não garante resultado futuro.
- Este sistema não executa ordens reais de compra ou venda.
- Indicadores e backtests têm limitações inerentes (look-ahead bias, overfitting, custos).
- A IA gera texto analítico baseado apenas nos dados calculados pelo sistema; não inventa preços ou eventos.
- Não use este sistema como única fonte para decisões financeiras reais.

---

## Licença

MIT
