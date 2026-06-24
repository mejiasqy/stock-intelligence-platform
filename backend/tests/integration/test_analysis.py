"""Testes de integração dos endpoints de análise e do fluxo pós-ingestão."""

from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.core.config import settings


def _minimal_ohlcv(n: int) -> pd.DataFrame:
    """Série OHLCV sintética com n candles em ordem cronológica."""
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


# ---------------------------------------------------------------------------
# GET /assets/{symbol}/analysis — sem snapshot
# ---------------------------------------------------------------------------


def test_get_analysis_asset_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/assets/NOTFOUND.SA/analysis")
    assert response.status_code == 404
    assert response.json()["detail"] == "asset_not_found"


def test_get_analysis_no_snapshot(client: TestClient) -> None:
    client.post("/api/v1/assets", json={"symbol": "NOSNAP.SA", "name": "No Snap Corp"})
    response = client.get("/api/v1/assets/NOSNAP.SA/analysis")
    assert response.status_code == 404
    assert response.json()["detail"] == "no_snapshot_available"


# ---------------------------------------------------------------------------
# POST /assets/ingestion/run + cálculo automático de snapshot
# ---------------------------------------------------------------------------


def test_ingestion_creates_snapshot(client: TestClient) -> None:
    """Ingestão com candles novos deve gerar snapshot automaticamente."""
    df = _minimal_ohlcv(10)
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post("/api/v1/assets/ingestion/run", json={"symbol": "AUTO3.SA", "days": 30})

    response = client.get("/api/v1/assets/AUTO3.SA/analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "partial", "insufficient_data")
    assert data["candles_used"] == 10
    assert data["calculation_version"] is not None


def test_ingestion_idempotent_does_not_create_snapshot(client: TestClient) -> None:
    """Segunda ingestão sem candles novos (inserted=0) não deve duplicar snapshot."""
    df = _minimal_ohlcv(5)
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post("/api/v1/assets/ingestion/run", json={"symbol": "IDEM3.SA", "days": 30})
        client.post("/api/v1/assets/ingestion/run", json={"symbol": "IDEM3.SA", "days": 30})

    # Snapshot existe mas é único (upsert)
    response = client.get("/api/v1/assets/IDEM3.SA/analysis")
    assert response.status_code == 200
    assert response.json()["candles_used"] == 5


def test_snapshot_status_partial_with_few_candles(client: TestClient) -> None:
    """10 candles → status partial (indicadores de período longo ausentes)."""
    df = _minimal_ohlcv(10)
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post("/api/v1/assets/ingestion/run", json={"symbol": "FEW3.SA", "days": 30})

    data = client.get("/api/v1/assets/FEW3.SA/analysis").json()
    assert data["status"] == "partial"
    assert data["sma_20"] is None
    assert data["return_1d"] is not None
    assert "sma_20" in data["insufficient_fields"]


def test_snapshot_status_ok_with_sufficient_candles(client: TestClient) -> None:
    """70 candles → status ok, nenhum campo nulo, insufficient_fields vazio."""
    df = _minimal_ohlcv(70)
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post("/api/v1/assets/ingestion/run", json={"symbol": "FULL3.SA", "days": 365})

    data = client.get("/api/v1/assets/FULL3.SA/analysis").json()
    assert data["status"] == "ok"
    assert data["insufficient_fields"] is None or data["insufficient_fields"] == {}
    assert data["sma_50"] is not None
    assert data["macd"] is not None


# ---------------------------------------------------------------------------
# POST /assets/{symbol}/analysis/recalculate
# ---------------------------------------------------------------------------


def test_recalculate_requires_api_key(client: TestClient) -> None:
    client.post("/api/v1/assets", json={"symbol": "RECALC.SA", "name": "Recalc Corp"})
    response = client.post("/api/v1/assets/RECALC.SA/analysis/recalculate")
    assert response.status_code == 422  # header X-Api-Key ausente


def test_recalculate_rejects_wrong_key(client: TestClient) -> None:
    client.post("/api/v1/assets", json={"symbol": "BADKEY.SA", "name": "Bad Key Corp"})
    response = client.post(
        "/api/v1/assets/BADKEY.SA/analysis/recalculate",
        headers={"X-Api-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_recalculate_with_correct_key(client: TestClient) -> None:
    """Recálculo explícito com chave correta deve retornar snapshot."""
    df = _minimal_ohlcv(10)
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post("/api/v1/assets/ingestion/run", json={"symbol": "RKEY3.SA", "days": 30})

    response = client.post(
        "/api/v1/assets/RKEY3.SA/analysis/recalculate",
        headers={"X-Api-Key": settings.api_secret_key},
    )
    assert response.status_code == 200
    assert response.json()["candles_used"] == 10


def test_recalculate_asset_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/assets/GHOST.SA/analysis/recalculate",
        headers={"X-Api-Key": settings.api_secret_key},
    )
    assert response.status_code == 404


def test_get_analysis_read_only_does_not_recalculate(client: TestClient) -> None:
    """GET /analysis não deve criar snapshot — deve retornar 404 se não existir."""
    client.post("/api/v1/assets", json={"symbol": "READONLY.SA", "name": "Readonly Corp"})
    r1 = client.get("/api/v1/assets/READONLY.SA/analysis")
    assert r1.status_code == 404

    # Mesmo após criar asset, sem ingestão não há snapshot
    r2 = client.get("/api/v1/assets/READONLY.SA/analysis")
    assert r2.status_code == 404
