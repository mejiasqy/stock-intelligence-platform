# API Reference — Stock Intelligence Platform

Base URL: `http://localhost:8000/api/v1`

Documentação interativa: `http://localhost:8000/docs` (Swagger UI)

> **Aviso:** este sistema é educacional e analítico. Não executa ordens de compra/venda e não constitui recomendação financeira.

---

## Sumário

- [Autenticação](#autenticação)
- [Envelope de erro](#envelope-de-erro)
- [Paginação](#paginação)
- [Request ID](#request-id)
- [CORS](#cors)
- [Rate Limiting](#rate-limiting)
- [Endpoints — Health](#health)
- [Endpoints — Assets](#assets)
- [Endpoints — Analysis](#analysis)
- [Endpoints — Signals e Rankings](#signals-e-rankings)
- [Endpoints — Backtests](#backtests)

---

## Autenticação

Endpoints de **leitura** (`GET`) são públicos e não exigem autenticação. Endpoints **mutáveis** (`POST`) exigem o header `X-Api-Key` com o valor configurado em `API_SECRET_KEY`.

```http
POST /api/v1/assets HTTP/1.1
X-Api-Key: <seu-valor-de-API_SECRET_KEY>
Content-Type: application/json
```

Sem o header ou com valor inválido:

```json
HTTP/1.1 401 Unauthorized

{
  "error": {
    "code": "unauthorized",
    "message": "Authentication required. Provide a valid X-Api-Key header.",
    "request_id": "a1b2c3d4-..."
  }
}
```

> **Endpoints que exigem `X-Api-Key`:**
> - `POST /api/v1/assets`
> - `POST /api/v1/assets/ingestion/run`
> - `POST /api/v1/assets/{symbol}/analysis/recalculate`
> - `POST /api/v1/assets/{symbol}/signal/recalculate`
> - `POST /api/v1/backtests/run`

---

## Envelope de erro

Todos os erros seguem o mesmo envelope:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "request_id": "string | null",
    "fields": [
      {
        "field": "body.symbol",
        "message": "String should match pattern ...",
        "type": "string_pattern_mismatch"
      }
    ]
  }
}
```

O campo `fields` aparece apenas em respostas `422` e contém os erros de validação de entrada. Mensagens de erro **nunca** expõem stack traces, SQL ou variáveis de ambiente.

### Códigos de erro

| Código | Status HTTP | Descrição |
|---|---|---|
| `unauthorized` | 401 | API key ausente ou inválida |
| `asset_not_found` | 404 | Ativo não encontrado |
| `asset_already_exists` | 409 | Símbolo já cadastrado |
| `no_snapshot_available` | 404 | Nenhuma análise disponível para o ativo |
| `no_signal_available` | 404 | Nenhum sinal disponível para o ativo |
| `backtest_run_not_found` | 404 | Execução de backtest não encontrada |
| `unknown_strategy` | 422 | Estratégia de backtest desconhecida |
| `validation_error` | 422 | Parâmetros de entrada inválidos |
| `rate_limit_exceeded` | 429 | Muitas requisições — aguarde e tente novamente |
| `internal_server_error` | 500 | Erro interno (detalhe não exposto) |

---

## Paginação

Todos os endpoints de listagem retornam respostas paginadas:

```json
{
  "items": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 143
  }
}
```

### Parâmetros

| Parâmetro | Tipo | Padrão | Máximo | Descrição |
|---|---|---|---|---|
| `limit` | int | 50 | 100 (trades: 500) | Itens por página |
| `offset` | int | 0 | — | Número de itens a pular |

Valores fora dos limites retornam `422 validation_error`.

```
GET /api/v1/assets?limit=20&offset=40
```

---

## Request ID

Cada requisição recebe um ID único propagado pelo header `X-Request-ID`.

- Se o cliente enviar `X-Request-ID`, o valor é ecoado na resposta.
- Se ausente, um UUID v4 é gerado automaticamente.
- O `request_id` é incluído no corpo de **todas** as respostas de erro.

```http
GET /api/v1/assets HTTP/1.1
X-Request-ID: meu-trace-id-123
```

```http
HTTP/1.1 200 OK
X-Request-ID: meu-trace-id-123
```

---

## CORS

O CORS é configurado via variáveis de ambiente. Os padrões para desenvolvimento são:

| Configuração | Padrão |
|---|---|
| Origins permitidas | `http://localhost:3000` |
| Métodos permitidos | `GET`, `POST`, `OPTIONS` |
| Headers permitidos | `Content-Type`, `X-Api-Key`, `X-Request-ID` |
| Credentials | `false` (nunca `allow-credentials: true`) |

Em produção, configure `CORS_ORIGINS` com o domínio real. Nunca use `*` em produção.

---

## Rate Limiting

O rate limiting é local, por instância de processo, por IP (não distribuído). Os limites reiniciam quando o processo é reiniciado. Não substitui autenticação nem protege contra ataques distribuídos.

| Endpoint | Limite padrão |
|---|---|
| Geral (não listado abaixo) | 120 req/minuto |
| `GET /rankings` | 30 req/minuto |
| `GET /assets/{symbol}/analysis` | 30 req/minuto |
| `POST /assets`, `/ingestion/run`, `/signal/recalculate` | 20 req/minuto |
| `POST /assets/ingestion/run` | 10 req/minuto |
| `POST /backtests/run` | 10 req/minuto |

Ao exceder o limite:

```json
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests. Please slow down.",
    "request_id": "..."
  }
}
```

Limites podem ser ajustados via variáveis de ambiente (ex.: `RATE_LIMIT_BACKTESTS=5/minute`). Consulte `.env.example`.

---

## Health

### `GET /health`

Verifica se o processo está vivo. Sem autenticação.

```json
{ "status": "ok", "version": "0.1.0" }
```

### `GET /ready`

Verifica dependências essenciais. Sem autenticação. Nunca retorna 5xx — banco indisponível retorna `degraded`.

```json
{ "status": "ok", "database": "connected" }
```

```json
{ "status": "degraded", "database": "unavailable" }
```

---

## Assets

### `GET /api/v1/assets`

Lista todos os ativos cadastrados. Sem autenticação.

**Query params:** `limit` (1–100, padrão 50), `offset` (≥0, padrão 0)

**Resposta 200:**
```json
{
  "items": [
    {
      "id": 1,
      "symbol": "PETR4.SA",
      "name": "Petróleo Brasileiro S.A.",
      "exchange": "B3",
      "created_at": "2026-06-25T10:00:00Z"
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 5 }
}
```

---

### `POST /api/v1/assets`

Cadastra um novo ativo. Exige `X-Api-Key`.

**Body:**
```json
{ "symbol": "VALE3.SA", "name": "Vale S.A.", "exchange": "B3" }
```

**Resposta 201:**
```json
{
  "id": 2,
  "symbol": "VALE3.SA",
  "name": "Vale S.A.",
  "exchange": "B3",
  "created_at": "2026-06-25T10:01:00Z"
}
```

**Erros:** `401 unauthorized`, `409 asset_already_exists`, `422 validation_error`

---

### `GET /api/v1/assets/{symbol}/prices`

Histórico de preços OHLCV do ativo. Sem autenticação.

**Query params:** `limit` (1–100), `offset`

**Resposta 200:**
```json
{
  "items": [
    {
      "timestamp": "2026-06-24T00:00:00Z",
      "open": 38.50, "high": 39.10, "low": 38.20,
      "close": 38.90, "volume": 12500000
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 252 }
}
```

**Erros:** `404 asset_not_found`, `422 validation_error`

---

### `POST /api/v1/assets/ingestion/run`

Ingere dados históricos do ativo via provedor de mercado (yfinance). Exige `X-Api-Key`. Rate limit: 10/minuto.

**Body:**
```json
{ "symbol": "PETR4.SA", "days": 365 }
```

**Resposta 200:**
```json
{
  "symbol": "PETR4.SA",
  "inserted": 248,
  "skipped": 0,
  "analysis_recalculated": true
}
```

**Erros:** `401 unauthorized`, `422 validation_error`

---

## Analysis

### `GET /api/v1/assets/{symbol}/analysis`

Retorna o snapshot de indicadores técnicos mais recente. Sem autenticação. Rate limit: 30/minuto.

**Resposta 200:**
```json
{
  "id": 15,
  "asset_id": 1,
  "timestamp": "2026-06-24T00:00:00Z",
  "status": "ok",
  "sma_20": 38.12, "sma_50": 36.90, "ema_20": 38.45,
  "rsi_14": 61.3,
  "macd": 0.52, "macd_signal": 0.38, "macd_histogram": 0.14,
  "bollinger_upper": 40.10, "bollinger_middle": 38.12, "bollinger_lower": 36.14,
  "vol_annualized_20d": 0.28,
  "max_drawdown_60d": -0.09,
  "return_1d": 0.005,
  "calculation_version": "1.0.0"
}
```

**Status possíveis:** `ok` (todos os indicadores disponíveis), `partial` (histórico parcial), `insufficient_data` (<2 candles)

**Erros:** `404 asset_not_found`, `404 no_snapshot_available`

---

### `POST /api/v1/assets/{symbol}/analysis/recalculate`

Força recálculo dos indicadores. Exige `X-Api-Key`.

**Resposta 200:** mesmo formato do `GET /analysis`

**Erros:** `401 unauthorized`, `404 asset_not_found`

---

## Signals e Rankings

### `GET /api/v1/assets/{symbol}/signal`

Retorna o sinal analítico mais recente do ativo. Sem autenticação.

**Resposta 200:**
```json
{
  "id": 8,
  "asset_id": 1,
  "signal_type": "bullish",
  "strength": 0.42,
  "score": 71.0,
  "reason_codes": {
    "price_above_sma_20": true,
    "sma_20_above_sma_50": true,
    "rsi_in_bullish_range": true
  },
  "pillar_scores": {
    "trend": 82.0,
    "momentum": 68.0,
    "volume": 55.0,
    "risk": 60.0,
    "structure": 70.0
  },
  "strategy_version": "1.0.0",
  "calculated_at": "2026-06-24T10:00:00Z"
}
```

> **Aviso:** sinais são instrumentos analíticos baseados em dados históricos — não são recomendações de investimento.

**Erros:** `404 asset_not_found`, `404 no_signal_available`

---

### `POST /api/v1/assets/{symbol}/signal/recalculate`

Força recálculo do sinal. Exige `X-Api-Key`.

**Resposta 200:** mesmo formato do `GET /signal`

**Erros:** `401 unauthorized`, `404 asset_not_found`

---

### `GET /api/v1/rankings`

Lista todos os ativos que possuem sinal, ordenados por `score` decrescente. Sem autenticação. Rate limit: 30/minuto.

**Query params:**
| Parâmetro | Tipo | Descrição |
|---|---|---|
| `limit` | int | 1–100, padrão 50 |
| `offset` | int | ≥0, padrão 0 |
| `signal_type` | `bullish` \| `bearish` \| `neutral` | Filtro por tipo de sinal |
| `min_score` | float | Score mínimo (0–100) |
| `max_score` | float | Score máximo (0–100) |
| `sort_by` | `score` \| `calculated_at` | Campo de ordenação (padrão: `score`) |
| `sort_order` | `asc` \| `desc` | Direção da ordenação (padrão: `desc`) |

**Resposta 200:**
```json
{
  "items": [
    {
      "asset_id": 1,
      "symbol": "PETR4.SA",
      "signal_type": "bullish",
      "score": 71.0,
      "strength": 0.42,
      "strategy_version": "1.0.0",
      "calculated_at": "2026-06-24T10:00:00Z"
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 3 }
}
```

**Erros:** `422 validation_error` (signal_type inválido)

---

## Backtests

### `POST /api/v1/backtests/run`

Executa um backtest. Parâmetros são persistidos para reprodutibilidade. Exige `X-Api-Key`. Rate limit: 10/minuto.

**Body:**
```json
{
  "symbol": "PETR4.SA",
  "strategy_name": "sma_crossover",
  "initial_capital": 100000,
  "transaction_cost_bps": 10,
  "slippage_bps": 10,
  "risk_free_rate_pct": 0.0,
  "start_date": "2023-01-01",
  "end_date": "2024-12-31"
}
```

Todos os campos exceto `symbol` são opcionais. `start_date` deve ser anterior a `end_date`.

**Resposta 200:**
```json
{
  "id": 12,
  "asset_id": 1,
  "strategy_name": "sma_crossover",
  "strategy_version": "1.0.0",
  "engine_version": "1.0.0",
  "status": "completed",
  "initial_capital": 100000.0,
  "final_equity": 113420.50,
  "total_return_pct": 13.42,
  "sharpe_ratio": 1.21,
  "max_drawdown_pct": -8.34,
  "trade_count": 7,
  "parameters_snapshot_json": {
    "transaction_cost_bps": 10,
    "slippage_bps": 10,
    "risk_free_rate_pct": 0.0
  },
  "created_at": "2026-06-25T10:00:00Z"
}
```

**Status possíveis:** `completed`, `insufficient_data`

**Erros:** `401 unauthorized`, `404 asset_not_found`, `422 unknown_strategy`, `422 validation_error`

---

### `GET /api/v1/backtests`

Histórico de backtests paginado. Sem autenticação.

**Query params:**
| Parâmetro | Tipo | Descrição |
|---|---|---|
| `limit` | int | 1–100, padrão 50 |
| `offset` | int | ≥0, padrão 0 |
| `symbol` | string | Filtrar por símbolo do ativo |
| `strategy_name` | string | Filtrar por nome da estratégia |

**Resposta 200:**
```json
{
  "items": [
    {
      "id": 12,
      "asset_id": 1,
      "strategy_name": "sma_crossover",
      "strategy_version": "1.0.0",
      "engine_version": "1.0.0",
      "status": "completed",
      "initial_capital": 100000.0,
      "total_return_pct": 13.42,
      "sharpe_ratio": 1.21,
      "max_drawdown_pct": -8.34,
      "trade_count": 7,
      "created_at": "2026-06-25T10:00:00Z"
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 1 }
}
```

> Nota: `equity_curve_json` não é retornado nesta listagem. Use `GET /backtests/{run_id}` para obter o resultado completo.

---

### `GET /api/v1/backtests/{run_id}`

Retorna o resultado completo de um backtest (inclui `equity_curve_json`). Sem autenticação.

**Resposta 200:** mesmo formato do `POST /backtests/run`, com o campo adicional `equity_curve_json`.

**Erros:** `404 backtest_run_not_found`

---

### `GET /api/v1/backtests/{run_id}/trades`

Lista as operações simuladas do backtest. Sem autenticação.

**Query params:** `limit` (1–**500**, padrão 50), `offset`

**Resposta 200:**
```json
{
  "items": [
    {
      "id": 1,
      "entry_timestamp": "2023-03-15T00:00:00Z",
      "exit_timestamp": "2023-04-10T00:00:00Z",
      "entry_price": 35.40,
      "exit_price": 38.20,
      "quantity": 282,
      "gross_pnl": 789.60,
      "net_pnl": 713.04,
      "reason_entry": "sma_crossover_bullish",
      "reason_exit": "sma_crossover_bearish"
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 7 }
}
```

> Limite máximo para trades é **500** por página (vs. 100 para demais endpoints), pois um backtest pode gerar muitas operações.

**Erros:** `404 backtest_run_not_found`, `422 validation_error`

---

## Notas gerais

- Todos os timestamps são em UTC (`Z`).
- Campos com valor `null` indicam dados insuficientes — nunca são omitidos silenciosamente.
- Endpoints de leitura não produzem efeitos colaterais.
- Performance passada não garante resultado futuro.
- Nenhum endpoint executa ou sugere ordens reais de compra/venda.
