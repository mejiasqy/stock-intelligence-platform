# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

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
