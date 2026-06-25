# Screenshots — Sprint 6

Screenshots capturados automaticamente via Playwright com dados reais, em 2026-06-25.

## Ambiente durante a captura

- Backend: FastAPI `v0.1.0` em `http://localhost:8000`
- Banco: PostgreSQL 16 (Docker) — saudável
- Frontend: Next.js 16.2.9 em `http://localhost:3000`
- Dados: 5 ativos demo (BBDC4.SA, ITUB4.SA, PETR4.SA, VALE3.SA, MGLU3.SA) + 2 de testes anteriores
- Sinais gerados: BBDC4.SA bullish 64, ITUB4.SA bullish 62, PETR4.SA bearish 34, VALE3.SA bearish 33, MGLU3.SA bearish 15
- Backtests: 4 execuções (PETR4 +12.20%, ITUB4 +5.37%, VALE3 -6.18%, BBDC4 -17.86%)

## Arquivos gerados

| Arquivo | URL capturada | Estado demonstrado | Dados reais |
|---|---|---|---|
| `01-overview.png` | `/` (1280×800) | Sucesso — 10 ativos, 2 bullish, 5 bearish, API Online | sim |
| `02-watchlist-all.png` | `/watchlist` (1280×800) | Tabela completa sem filtro | sim |
| `03-watchlist-bullish.png` | `/watchlist` filtro "Alta" | Apenas ativos com sinal bullish | sim |
| `04-watchlist-bearish.png` | `/watchlist` filtro "Baixa" | Apenas ativos com sinal bearish | sim |
| `05-asset-detail-itub4.png` | `/assets/ITUB4.SA` (1280×800) | Score 62, bullish, 250 candles, gráfico de fechamento, indicadores técnicos, reason_codes | sim |
| `06-asset-detail-mglu3.png` | `/assets/MGLU3.SA` (1280×800) | Score 15, bearish, volume pilar zero | sim |
| `07-asset-detail-error.png` | `/assets/NOSUCH.SA` (1280×800) | Estado de erro — "Asset not found" (404) | sim (erro real do banco) |
| `08-backtests-list.png` | `/backtests` (1280×800) | Lista de 4 runs com símbolo, retorno, Sharpe, DD | sim |
| `09-backtests-detail.png` | `/backtests` PETR4 expandido | Curva de patrimônio, métricas completas, 3 trades simulados | sim |
| `10-overview-mobile.png` | `/` (390×844 mobile) | Overview responsivo em viewport mobile | sim |
| `11-watchlist-mobile.png` | `/watchlist` (390×844 mobile) | Watchlist responsiva em viewport mobile | sim |

## Notas de limitação documentadas

- **Colunas Preço/Variação/Volatilidade na Watchlist** exibem "—": esses campos não são parte de `RankingEntry` na API atual. Nota explicativa exibida na interface.
- **SMA/EMA no gráfico**: exibidos como valores pontuais nos cards de indicadores; série histórica indisponível nesta versão da API.
- **Histórico de sinais**: exibido como "indisponível nesta versão" — sem endpoint de série histórica de sinais na Sprint 6.
- **Curva de patrimônio em modo headless**: eixos e legendas renderizados corretamente; traçado das linhas tênue em captura headless (comportamento esperado do Recharts sem interação de viewport) — visual correto no browser real.

## Como reproduzir

```powershell
# 1. Subir banco e backend
docker compose up -d db
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Subir frontend
cd ../frontend
npm run dev

# 3. Executar script de screenshots (Playwright)
# O script está em docs/screenshots/take-screenshots.mjs (ou regenerar pelo histórico de sessão)
```

## Validação de segurança e contratos (Sprint 6)

| Verificação | Resultado |
|---|---|
| X-Api-Key no frontend (bundle, env.local, código) | Não encontrado — ✓ |
| Chamadas POST/PUT/DELETE no frontend | Não encontradas — ✓ |
| Endpoints administrativos chamados pelo browser | Nenhum — ✓ |
| Overview usa `calculated_at` do primeiro item de rankings | Não usa — ✓ |
| KPI "API" usa `/health` (dado confiável, não temporal) | Confirmado — ✓ |
| Todos os campos nullable → "—" (nunca "undefined" ou NaN) | Confirmado — ✓ |
