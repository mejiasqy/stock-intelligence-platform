# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### Added — Sprint 7 (2026-06-25)
- Geração de relatórios analíticos via LLM (Anthropic `claude-haiku-4-5-20251001`) com fallback determinístico
- Provider desacoplado por Protocol síncrono; fallback ativado automaticamente em timeout, erro ou saída inválida
- Fingerprint SHA-256 do contexto para idempotência de relatórios por ativo/tipo/data/contexto
- Validação da saída LLM em 5 camadas: parse JSON, schema, reason_codes, guardrails, factual
- Alertas informativos via Telegram: `SignalChangeRule`, `ScoreHighRule`, `ScoreLowRule`
- Deduplicação de alertas por janela de 24h; status `failed` não bloqueia retry
- Defaults seguros: `ALERTS_ENABLED=false`, `ALERTS_DRY_RUN=true`, `SCHEDULER_ENABLED=false`
- Job diário opt-in via `BackgroundScheduler` (APScheduler síncrono, thread-based)
- Advisory lock PostgreSQL session-level com conexão física dedicada (`engine.connect()` + `sessionmaker(bind=lock_conn)`)
- Endpoints: `GET /assets/{symbol}/report/latest`, `POST /assets/{symbol}/report/generate`, `POST /jobs/daily-pipeline/run`
- Migrations: `c9d0e1f2a3b4` (report_runs), `d5e6f7a8b9c0` (alert_log + alert_state)
- Constraint `uq_report_run_asset_type_date_fp` para idempotência de relatórios
- Índice `ix_alert_log_asset_rule_fired` em `(asset_id, rule_key, fired_at)` para deduplicação eficiente
- 63 novos testes (37 unitários + 24 integração); total 222 testes

### Added — Sprint 6 (2026-06-25)
- Dashboard Next.js com 4 páginas: Overview, Watchlist, Detalhe do ativo, Backtests
- Componentes UI: `StatusBadge`, `ScoreBar`, `LoadingSpinner`, `EmptyState`, `ErrorState`
- Gráficos: `PriceChart` (fechamento histórico real) e `EquityCurveChart` (equity vs buy-and-hold)
- Camada de API tipada em `src/lib/api.ts` com `ApiError` e envelope de erro normalizado
- 35 testes Vitest (componentes, contratos de API, estados de insufficient_data)
- Campo `symbol: str` adicionado a `BacktestRunSummary` via JOIN com Asset no endpoint `GET /api/v1/backtests`
- `Navbar`, `Disclaimer` global e `QueryClientProvider` no layout raiz
- Diretório `docs/screenshots/` com README de validação

### Changed — Sprint 6
- `backend/app/schemas/backtest.py`: `BacktestRunSummary` inclui `symbol`
- `backend/app/api/routers/backtests.py`: `list_backtest_runs` usa JOIN com Asset
- `frontend/src/app/layout.tsx`: integrado Providers, Navbar e Disclaimer
- `frontend/src/app/page.tsx`: substituído placeholder por Overview com dados reais

### Added — Sprint 0–5
- Estrutura inicial do repositório (Sprint 0)
- Documentação base: `README.md`, `PROJECT_CONTEXT.md`, `AUTOMATION_PROGRESS.md`
- Ambiente Docker com PostgreSQL 16
- Backend FastAPI com endpoints `/health` e `/ready`
- Frontend Next.js 15 com App Router e Tailwind CSS
- Pipeline de CI com GitHub Actions (backend e frontend)
- Configuração de qualidade: Ruff, mypy, ESLint, TypeScript
- Script de verificação de ambiente (`scripts/verify_environment.py`)

---

## [0.1.0] — Sprint 0 — Em andamento

Sprint 0: Fundação e governança — estrutura, ambiente, CI e documentação base.
