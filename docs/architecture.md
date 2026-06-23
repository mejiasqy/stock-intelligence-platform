# Arquitetura — Stock Intelligence Platform

## Diagrama de alto nível

```
                    ┌──────────────────────────────┐
                    │     Mercado / Data Provider   │
                    └───────────────┬──────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │    Data Ingestion Service    │
                     │  normalização + validações   │
                     └───────────────┬─────────────┘
                                    │
         ┌──────────────────────────▼──────────────────────────┐
         │                    PostgreSQL 16                     │
         │  assets | price_bars | indicators | signals |       │
         │  backtest_runs | backtest_trades | report_runs      │
         └──────────────────────────┬──────────────────────────┘
                                    │
      ┌─────────────────────────────▼──────────────────────────────┐
      │                    Analysis Domain                         │
      │  indicadores | scoring | sinais | risco | backtesting      │
      └─────────────────────┬───────────────────────┬─────────────┘
                            │                       │
             ┌──────────────▼─────────────┐ ┌──────▼─────────────┐
             │      FastAPI REST API       │ │  Scheduler / Alerts │
             │  /api/v1/* + OpenAPI docs  │ │  Telegram / e-mail  │
             └──────────────┬─────────────┘ └────────────────────┘
                            │
                 ┌──────────▼──────────┐
                 │  Next.js Dashboard  │
                 │  App Router + TS    │
                 └─────────────────────┘
```

## Princípios de design

1. **Separação de responsabilidades** — coleta, domínio, API, banco, jobs e UI em camadas distintas.
2. **Testabilidade** — lógica de indicadores, scoring e backtest em funções puras sempre que possível.
3. **Auditabilidade** — todo score e sinal registra os fatores de origem (`reason_codes`).
4. **Reprodutibilidade** — backtest registra parâmetros, período e custos simulados.
5. **Fail closed** — dados insuficientes retornam estado explícito, nunca análise inventada.
6. **Segurança por padrão** — segredos fora do Git, validação em todas as entradas.
7. **Evolução incremental** — cada sprint entrega algo executável e validado.

## Stack

| Camada | Tecnologia | Versão mínima |
|---|---|---|
| Backend | Python | 3.12 |
| Framework API | FastAPI | 0.115 |
| ORM | SQLAlchemy | 2.0 |
| Migrations | Alembic | 1.14 |
| Banco | PostgreSQL | 16 |
| Frontend | Next.js | 15 (App Router) |
| Linguagem frontend | TypeScript | 5 |
| Estilos | Tailwind CSS | 3 |
| Infra dev | Docker Compose | v2+ |
| CI | GitHub Actions | — |
| Pacotes Python | uv | 0.11+ |
| Lint/format | Ruff | 0.8+ |
| Typecheck backend | mypy | 1.13+ |

## Estrutura de módulos

```
backend/app/
├── api/          ← routers e dependencies (sem lógica de negócio)
├── core/         ← config, logging, segurança
├── db/           ← base declarativa, session, migrations
├── domain/       ← indicadores, scoring, sinais, backtest, reports (Sprint 1+)
├── services/     ← orquestração entre camadas (Sprint 1+)
├── providers/    ← adaptadores externos: market data, LLM (Sprint 1+)
├── jobs/         ← jobs agendados (Sprint 7+)
└── schemas/      ← Pydantic schemas de I/O da API (Sprint 1+)
```

## Decisões arquiteturais

Consulte o arquivo `AUTOMATION_PROGRESS.md` — seção "Decisões arquiteturais" — para o log de ADRs.
