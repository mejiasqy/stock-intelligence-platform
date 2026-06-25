"""Testes de integração dos endpoints de backtesting."""

from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.core.config import settings

API_KEY = settings.api_secret_key


def _ohlcv(n: int, start_price: float = 10.0, step: float = 0.0) -> pd.DataFrame:
    dates = pd.date_range("2023-01-02", periods=n, freq="B", tz="UTC")
    prices = [start_price + i * step for i in range(n)]
    return pd.DataFrame(
        {
            "timestamp": dates,
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1_000_000] * n,
        }
    )


def _ohlcv_with_crossover(n: int = 80) -> pd.DataFrame:
    prices = [10.0] * 25 + [30.0] * 30 + [10.0] * (n - 55)
    prices = prices[:n]
    dates = pd.date_range("2023-01-02", periods=len(prices), freq="B", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": dates,
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1_000_000] * len(prices),
        }
    )


def _ingest(client: TestClient, symbol: str, df: pd.DataFrame) -> None:
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": symbol, "days": 365},
            headers={"X-Api-Key": API_KEY},
        )


# ---------------------------------------------------------------------------
# POST /api/v1/backtests/run
# ---------------------------------------------------------------------------


def test_run_backtest_unauthorized(client: TestClient) -> None:
    r = client.post("/api/v1/backtests/run", json={"symbol": "TEST.SA"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_run_backtest_wrong_key(client: TestClient) -> None:
    r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "TEST.SA"},
        headers={"X-Api-Key": "wrong"},
    )
    assert r.status_code == 401


def test_run_backtest_asset_not_found(client: TestClient) -> None:
    r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "NOTFOUND.SA"},
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "asset_not_found"


def test_run_backtest_unknown_strategy(client: TestClient) -> None:
    _ingest(client, "STRAT.SA", _ohlcv(60))
    r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "STRAT.SA", "strategy_name": "nonexistent"},
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unknown_strategy"


def test_run_backtest_insufficient_data(client: TestClient) -> None:
    _ingest(client, "SHORT.SA", _ohlcv(10))
    r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "SHORT.SA"},
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "insufficient_data"
    assert r.json()["trade_count"] is None


def test_run_backtest_creates_run(client: TestClient) -> None:
    _ingest(client, "BACK3.SA", _ohlcv_with_crossover())
    r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "BACK3.SA", "initial_capital": 50000},
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("completed", "insufficient_data")
    assert data["strategy_name"] == "sma_crossover"
    assert data["engine_version"] == "1.0.0"
    assert data["initial_capital"] == 50000.0
    snap = data["parameters_snapshot_json"]
    assert snap["transaction_cost_bps"] == 10
    assert snap["slippage_bps"] == 10
    assert snap["risk_free_rate_pct"] == 0.0


def test_run_backtest_parameters_persisted(client: TestClient) -> None:
    _ingest(client, "PARAM.SA", _ohlcv_with_crossover())
    r = client.post(
        "/api/v1/backtests/run",
        json={
            "symbol": "PARAM.SA",
            "transaction_cost_bps": 15,
            "slippage_bps": 20,
            "risk_free_rate_pct": 2.5,
        },
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 200
    snap = r.json()["parameters_snapshot_json"]
    assert snap["transaction_cost_bps"] == 15
    assert snap["slippage_bps"] == 20
    assert snap["risk_free_rate_pct"] == 2.5


def test_run_backtest_invalid_dates(client: TestClient) -> None:
    _ingest(client, "DATES.SA", _ohlcv_with_crossover())
    r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "DATES.SA", "start_date": "2024-12-31", "end_date": "2024-01-01"},
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


# ---------------------------------------------------------------------------
# GET /api/v1/backtests
# ---------------------------------------------------------------------------


def test_list_backtests_empty(client: TestClient) -> None:
    r = client.get("/api/v1/backtests")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["pagination"]["total"] == 0


def test_list_backtests_item_has_symbol(client: TestClient) -> None:
    _ingest(client, "SYMB.SA", _ohlcv_with_crossover())
    client.post("/api/v1/backtests/run", json={"symbol": "SYMB.SA"}, headers={"X-Api-Key": API_KEY})
    r = client.get("/api/v1/backtests")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert items[0]["symbol"] == "SYMB.SA"


def test_list_backtests_filter_by_symbol(client: TestClient) -> None:
    _ingest(client, "LST1.SA", _ohlcv_with_crossover())
    _ingest(client, "LST2.SA", _ohlcv_with_crossover())
    client.post("/api/v1/backtests/run", json={"symbol": "LST1.SA"}, headers={"X-Api-Key": API_KEY})
    client.post("/api/v1/backtests/run", json={"symbol": "LST2.SA"}, headers={"X-Api-Key": API_KEY})

    r = client.get("/api/v1/backtests?symbol=LST1.SA")
    assert r.status_code == 200
    body = r.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["strategy_name"] == "sma_crossover"
    assert body["items"][0]["symbol"] == "LST1.SA"


def test_list_backtests_pagination_meta(client: TestClient) -> None:
    _ingest(client, "PMETA.SA", _ohlcv_with_crossover())
    client.post(
        "/api/v1/backtests/run", json={"symbol": "PMETA.SA"}, headers={"X-Api-Key": API_KEY}
    )
    client.post(
        "/api/v1/backtests/run", json={"symbol": "PMETA.SA"}, headers={"X-Api-Key": API_KEY}
    )

    r = client.get("/api/v1/backtests?limit=1&offset=0")
    body = r.json()
    assert body["pagination"]["total"] == 2
    assert len(body["items"]) == 1


# ---------------------------------------------------------------------------
# GET /api/v1/backtests/{run_id}
# ---------------------------------------------------------------------------


def test_get_backtest_run_not_found(client: TestClient) -> None:
    r = client.get("/api/v1/backtests/99999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "backtest_run_not_found"


def test_get_backtest_run_returns_data(client: TestClient) -> None:
    _ingest(client, "GETB.SA", _ohlcv_with_crossover())
    run_r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "GETB.SA"},
        headers={"X-Api-Key": API_KEY},
    )
    run_id = run_r.json()["id"]
    r = client.get(f"/api/v1/backtests/{run_id}")
    assert r.status_code == 200
    assert r.json()["id"] == run_id


# ---------------------------------------------------------------------------
# GET /api/v1/backtests/{run_id}/trades
# ---------------------------------------------------------------------------


def test_get_backtest_trades_not_found(client: TestClient) -> None:
    r = client.get("/api/v1/backtests/99999/trades")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "backtest_run_not_found"


def test_get_backtest_trades_returns_paginated(client: TestClient) -> None:
    _ingest(client, "TRAD.SA", _ohlcv_with_crossover())
    run_r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "TRAD.SA"},
        headers={"X-Api-Key": API_KEY},
    )
    run_id = run_r.json()["id"]
    r = client.get(f"/api/v1/backtests/{run_id}/trades")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["items"], list)
    assert "pagination" in body


# ---------------------------------------------------------------------------
# Reprodutibilidade
# ---------------------------------------------------------------------------


def test_run_backtest_reproducible(client: TestClient) -> None:
    _ingest(client, "REPR.SA", _ohlcv_with_crossover())
    body = {"symbol": "REPR.SA", "initial_capital": 100000}
    headers = {"X-Api-Key": API_KEY}

    r1 = client.post("/api/v1/backtests/run", json=body, headers=headers).json()
    r2 = client.post("/api/v1/backtests/run", json=body, headers=headers).json()

    assert r1["status"] == r2["status"]
    assert r1["trade_count"] == r2["trade_count"]
    if r1["total_return_pct"] is not None:
        assert abs(r1["total_return_pct"] - r2["total_return_pct"]) < 0.001
