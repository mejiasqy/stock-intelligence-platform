# Modelo de dados — Stock Intelligence Platform

> Este documento será detalhado na Sprint 1 — Dados e banco.
> As entidades abaixo refletem o design planejado em `PROJECT_CONTEXT.md`.

## Entidades principais

| Entidade | Descrição | Sprint |
|---|---|---|
| `assets` | Ativo monitorado (símbolo, exchange, tipo) | 1 |
| `price_bars` | Série OHLCV normalizada por ativo e timeframe | 1 |
| `indicator_snapshots` | Snapshot calculado de indicadores por ativo/data | 2 |
| `signals` | Sinal analítico explicável com reason_codes | 3 |
| `strategy_configs` | Configurações versionadas de estratégia | 3 |
| `backtest_runs` | Execução reproduzível de backtest | 4 |
| `backtest_trades` | Operações simuladas dentro de um backtest | 4 |
| `watchlists` / `watchlist_items` | Organização de ativos | 5 |
| `report_runs` | Relatórios gerados com metadados | 7 |

## Índices principais planejados

- `price_bars`: índice único em `(asset_id, timeframe, timestamp, source)`
- `indicator_snapshots`: índice único em `(asset_id, timeframe, timestamp, calculation_version)`
- `signals`: índice em `(asset_id, timestamp)`

## Regras de migração

- Toda mudança de schema via Alembic (`alembic revision --autogenerate`)
- Nunca alterar schema diretamente em produção
- Migrations testadas em banco vazio antes de aplicar
- Este documento atualizado a cada sprint com mudança de banco
