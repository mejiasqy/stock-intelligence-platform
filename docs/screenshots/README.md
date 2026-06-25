# Screenshots — Sprint 6

Screenshots das 4 páginas do dashboard com dados reais.

## Como capturar

Com backend e frontend rodando:

```bash
# backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# frontend
cd frontend && npm run dev
```

Acessar em `http://localhost:3000` e capturar manualmente:

| Arquivo esperado | URL | Dados de demonstração |
|---|---|---|
| `overview.png` | `/` | 7 ativos no ranking, 2 bullish, 5 bearish |
| `watchlist.png` | `/watchlist` | Tabela com filtros por sinal |
| `watchlist-filter-bullish.png` | `/watchlist` (filtro ativo) | Apenas BBDC4 e ITUB4 |
| `asset-detail-itub4.png` | `/assets/ITUB4.SA` | Score 62, bullish, 250 candles |
| `asset-detail-insufficient.png` | `/assets/MGLU3.SA` | Score 15, bearish |
| `backtests.png` | `/backtests` | 4 runs com símbolo, retorno, Sharpe |
| `backtests-detail.png` | `/backtests` (run expandido) | Curva de patrimônio + trades |

## Validação realizada em 2026-06-25

Todos os endpoints verificados com dados reais:
- `GET /api/v1/rankings` → 7 ativos (5 demo + 2 de testes anteriores)
- `GET /api/v1/assets/ITUB4.SA/signal` → bullish, score 62, 20 reason_codes
- `GET /api/v1/assets/ITUB4.SA/analysis` → status ok, 250 candles
- `GET /api/v1/assets/ITUB4.SA/prices?limit=120` → 120 barras OHLCV
- `GET /api/v1/backtests` → 4 runs, campo `symbol` presente
- `GET /api/v1/backtests/1` → equity_curve_json com 250 pontos, 2 trades
