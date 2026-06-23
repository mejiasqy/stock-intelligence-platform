# API Reference — Stock Intelligence Platform

Base URL: `http://localhost:8000/api/v1`

Documentação interativa: `http://localhost:8000/docs` (Swagger UI)

---

## Endpoints implementados

### `GET /health`

Verifica se o processo está vivo.

**Resposta 200:**
```json
{ "status": "ok", "version": "0.1.0" }
```

---

### `GET /ready`

Verifica se as dependências essenciais estão disponíveis.

**Resposta 200 (banco conectado):**
```json
{ "status": "ok", "database": "connected" }
```

**Resposta 200 (banco indisponível — degradado, mas sem crash):**
```json
{ "status": "degraded", "database": "unavailable" }
```

---

## Endpoints planejados (Sprint 1+)

```
GET    /api/v1/assets
POST   /api/v1/assets
GET    /api/v1/assets/{symbol}
GET    /api/v1/assets/{symbol}/prices
GET    /api/v1/assets/{symbol}/analysis
GET    /api/v1/assets/{symbol}/signals
GET    /api/v1/rankings
POST   /api/v1/ingestion/run
POST   /api/v1/backtests/run
GET    /api/v1/backtests/{run_id}
GET    /api/v1/backtests/{run_id}/trades
POST   /api/v1/reports/generate
GET    /api/v1/watchlists
POST   /api/v1/watchlists
```

---

## Convenções

- Prefixo: `/api/v1`
- Formato: JSON em `snake_case`
- Erros padronizados: `{ "detail": "mensagem" }`
- Paginação em listas: `{ "items": [...], "total": N, "page": 1, "size": 20 }`
