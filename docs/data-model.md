# Modelo de dados — Stock Intelligence Platform

## Tabelas implementadas (Sprint 1)

### `assets`

Representa um ativo financeiro negociado em bolsa.

| Coluna | Tipo | Restrição | Descrição |
|---|---|---|---|
| `id` | INTEGER | PK, auto | Identificador interno |
| `symbol` | VARCHAR(20) | UNIQUE, NOT NULL | Ticker (ex: `PETR4.SA`) |
| `name` | VARCHAR(200) | NOT NULL | Nome do ativo |
| `exchange` | VARCHAR(50) | NOT NULL, default `B3` | Bolsa |
| `asset_type` | VARCHAR(20) | NOT NULL, default `stock` | Tipo (`stock`, `fii`, etc.) |
| `created_at` | TIMESTAMPTZ | NOT NULL, server default | Data de criação |

Índices: `ix_assets_id` (PK), `ix_assets_symbol` (UNIQUE).

---

### `price_bars`

Série histórica OHLCV diária de um ativo.

| Coluna | Tipo | Restrição | Descrição |
|---|---|---|---|
| `id` | INTEGER | PK, auto | Identificador interno |
| `asset_id` | INTEGER | FK → assets.id, NOT NULL | Ativo relacionado |
| `timestamp` | TIMESTAMPTZ | NOT NULL | Data/hora do candle (UTC) |
| `open` | NUMERIC(18,6) | NOT NULL | Preço de abertura |
| `high` | NUMERIC(18,6) | NOT NULL | Máxima |
| `low` | NUMERIC(18,6) | NOT NULL | Mínima |
| `close` | NUMERIC(18,6) | NOT NULL | Fechamento |
| `volume` | BIGINT | NOT NULL, default 0 | Volume negociado |
| `created_at` | TIMESTAMPTZ | NOT NULL, server default | Data de inserção |

Restrição de unicidade: `uq_price_bar_asset_ts` (`asset_id`, `timestamp`).
Índices: `ix_price_bars_id` (PK), `ix_price_bars_asset_id`.

---

## Ingestão idempotente

A ingestão usa `INSERT ... ON CONFLICT DO NOTHING` na constraint `uq_price_bar_asset_ts`.
Execuções repetidas para o mesmo ativo e período não duplicam registros.

Fonte padrão: **yfinance** (adaptador `YFinanceProvider`).
A interface `MarketDataProvider` (protocolo Python) permite trocar a fonte sem alterar o serviço.

---

## Endpoints (Sprint 1)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/assets` | Lista todos os ativos |
| POST | `/api/v1/assets` | Cria um ativo |
| GET | `/api/v1/assets/{symbol}/prices` | Série histórica paginada (padrão: 252 barras) |
| POST | `/api/v1/assets/ingestion/run` | Ingere histórico de um ativo via yfinance |

---

## Ativos de demo

Seed via `scripts/seed_demo_data.py`:

| Symbol | Empresa |
|---|---|
| PETR4.SA | Petrobras PN |
| VALE3.SA | Vale ON |
| ITUB4.SA | Itaú Unibanco PN |
| BBDC4.SA | Bradesco PN |
| MGLU3.SA | Magazine Luiza ON |

---

## Entidades planejadas (sprints futuras)

| Entidade | Descrição | Sprint |
|---|---|---|
| `indicator_snapshots` | Snapshot calculado de indicadores por ativo/data | 2 |
| `signals` | Sinal analítico explicável com reason_codes | 3 |
| `strategy_configs` | Configurações versionadas de estratégia | 3 |
| `backtest_runs` | Execução reproduzível de backtest | 4 |
| `backtest_trades` | Operações simuladas dentro de um backtest | 4 |
| `watchlists` / `watchlist_items` | Organização de ativos | 5 |
| `report_runs` | Relatórios gerados com metadados | 7 |

## Regras de migração

- Toda mudança de schema via Alembic (`alembic revision --autogenerate`)
- Nunca alterar schema diretamente em produção
- Migrations testadas em banco vazio antes de aplicar
- Este documento atualizado a cada sprint com mudança de banco
