"""Testes de integração dos endpoints de análise e do fluxo pós-ingestão."""

from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.core.config import settings

API_KEY = settings.api_secret_key


def _minimal_ohlcv(n: int) -> pd.DataFrame:
    dates = pd.date_range("2023-01-02", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": dates,
            "open": [30.0 + i * 0.1 for i in range(n)],
            "high": [31.0 + i * 0.1 for i in range(n)],
            "low": [29.0 + i * 0.1 for i in range(n)],
            "close": [30.5 + i * 0.1 for i in range(n)],
            "volume": [1_000_000] * n,
        }
    )


def _ingest(client: TestClient, symbol: str, n: int = 70) -> None:
    df = _minimal_ohlcv(n)
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
# GET /assets/{symbol}/analysis — sem snapshot
# ---------------------------------------------------------------------------


def test_get_analysis_asset_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/assets/NOTFOUND.SA/analysis")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "asset_not_found"


def test_get_analysis_no_snapshot(client: TestClient) -> None:
    client.post(
        "/api/v1/assets",
        json={"symbol": "NOSNAP.SA", "name": "No Snap Corp"},
        headers={"X-Api-Key": API_KEY},
    )
    response = client.get("/api/v1/assets/NOSNAP.SA/analysis")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_snapshot_available"


# ---------------------------------------------------------------------------
# POST /assets/ingestion/run + cálculo automático de snapshot
# ---------------------------------------------------------------------------


def test_ingestion_creates_snapshot(client: TestClient) -> None:
    _ingest(client, "AUTO3.SA", 10)
    response = client.get("/api/v1/assets/AUTO3.SA/analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "partial", "insufficient_data")
    assert data["candles_used"] == 10
    assert data["calculation_version"] is not None


def test_ingestion_idempotent_does_not_create_snapshot(client: TestClient) -> None:
    df = _minimal_ohlcv(5)
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "IDEM3.SA", "days": 30},
            headers={"X-Api-Key": API_KEY},
        )
        client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "IDEM3.SA", "days": 30},
            headers={"X-Api-Key": API_KEY},
        )

    response = client.get("/api/v1/assets/IDEM3.SA/analysis")
    assert response.status_code == 200
    assert response.json()["candles_used"] == 5


def test_snapshot_status_partial_with_few_candles(client: TestClient) -> None:
    _ingest(client, "FEW3.SA", 10)
    data = client.get("/api/v1/assets/FEW3.SA/analysis").json()
    assert data["status"] == "partial"
    assert data["sma_20"] is None
    assert data["return_1d"] is not None
    assert "sma_20" in data["insufficient_fields"]


def test_snapshot_status_ok_with_sufficient_candles(client: TestClient) -> None:
    _ingest(client, "FULL3.SA", 70)
    data = client.get("/api/v1/assets/FULL3.SA/analysis").json()
    assert data["status"] == "ok"
    assert data["insufficient_fields"] is None or data["insufficient_fields"] == {}
    assert data["sma_50"] is not None
    assert data["macd"] is not None


# ---------------------------------------------------------------------------
# POST /assets/{symbol}/analysis/recalculate
# ---------------------------------------------------------------------------


def test_recalculate_requires_api_key(client: TestClient) -> None:
    client.post(
        "/api/v1/assets",
        json={"symbol": "RECALC.SA", "name": "Recalc Corp"},
        headers={"X-Api-Key": API_KEY},
    )
    response = client.post("/api/v1/assets/RECALC.SA/analysis/recalculate")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_recalculate_rejects_wrong_key(client: TestClient) -> None:
    client.post(
        "/api/v1/assets",
        json={"symbol": "BADKEY.SA", "name": "Bad Key Corp"},
        headers={"X-Api-Key": API_KEY},
    )
    response = client.post(
        "/api/v1/assets/BADKEY.SA/analysis/recalculate",
        headers={"X-Api-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_recalculate_with_correct_key(client: TestClient) -> None:
    _ingest(client, "RKEY3.SA", 10)
    response = client.post(
        "/api/v1/assets/RKEY3.SA/analysis/recalculate",
        headers={"X-Api-Key": API_KEY},
    )
    assert response.status_code == 200
    assert response.json()["candles_used"] == 10


def test_recalculate_asset_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/assets/GHOST.SA/analysis/recalculate",
        headers={"X-Api-Key": API_KEY},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "asset_not_found"


def test_get_analysis_read_only_does_not_recalculate(client: TestClient) -> None:
    client.post(
        "/api/v1/assets",
        json={"symbol": "READONLY.SA", "name": "Readonly Corp"},
        headers={"X-Api-Key": API_KEY},
    )
    r1 = client.get("/api/v1/assets/READONLY.SA/analysis")
    assert r1.status_code == 404
    r2 = client.get("/api/v1/assets/READONLY.SA/analysis")
    assert r2.status_code == 404
