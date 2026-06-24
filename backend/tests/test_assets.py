"""Testes dos endpoints de assets e ingestão."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"], utc=True),
            "open": [30.0, 31.0, 32.0],
            "high": [31.0, 32.0, 33.0],
            "low": [29.0, 30.0, 31.0],
            "close": [30.5, 31.5, 32.5],
            "volume": [1000000, 1200000, 900000],
        }
    )


def test_list_assets_empty(client: TestClient) -> None:
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    assert response.json() == []


def test_create_asset(client: TestClient) -> None:
    payload = {"symbol": "TEST3.SA", "name": "Test Corp", "exchange": "B3"}
    response = client.post("/api/v1/assets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "TEST3.SA"
    assert data["exchange"] == "B3"


def test_create_asset_duplicate(client: TestClient) -> None:
    payload = {"symbol": "DUP3.SA", "name": "Dup Corp"}
    client.post("/api/v1/assets", json=payload)
    response = client.post("/api/v1/assets", json=payload)
    assert response.status_code == 409


def test_get_prices_asset_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/assets/NOTFOUND.SA/prices")
    assert response.status_code == 404


def test_get_prices_empty_history(client: TestClient) -> None:
    client.post("/api/v1/assets", json={"symbol": "EMPTY3.SA", "name": "Empty Corp"})
    response = client.get("/api/v1/assets/EMPTY3.SA/prices")
    assert response.status_code == 200
    assert response.json() == []


def test_ingestion_inserts_data(client: TestClient, sample_ohlcv: pd.DataFrame) -> None:
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=sample_ohlcv,
    ):
        response = client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "INGEST3.SA", "days": 365},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 3
    assert data["skipped"] == 0


def test_ingestion_idempotent(client: TestClient, sample_ohlcv: pd.DataFrame) -> None:
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=sample_ohlcv,
    ):
        client.post("/api/v1/assets/ingestion/run", json={"symbol": "IDEM3.SA", "days": 365})
        response = client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "IDEM3.SA", "days": 365},
        )
    data = response.json()
    assert data["inserted"] == 0
    assert data["skipped"] == 3


def test_ingestion_empty_provider(client: TestClient) -> None:
    empty_df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=empty_df,
    ):
        response = client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "NODATA3.SA", "days": 30},
        )
    assert response.status_code == 200
    assert response.json()["inserted"] == 0


def test_ingestion_invalid_symbol(client: TestClient) -> None:
    mock_provider = MagicMock()
    mock_provider.fetch_ohlcv.return_value = pd.DataFrame(
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    with patch("app.services.ingestion_service.YFinanceProvider", return_value=mock_provider):
        response = client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "XXXINVALID.SA", "days": 10},
        )
    assert response.status_code == 200
    assert response.json()["inserted"] == 0
