"""Testes de integração dos endpoints de sinais e rankings."""

from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.scoring.engine import SCORING_VERSION

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
# GET /assets/{symbol}/signal
# ---------------------------------------------------------------------------


def test_get_signal_asset_not_found(client: TestClient) -> None:
    r = client.get("/api/v1/assets/NOTFOUND.SA/signal")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "asset_not_found"


def test_get_signal_no_signal_yet(client: TestClient) -> None:
    client.post(
        "/api/v1/assets",
        json={"symbol": "NOSIG.SA", "name": "No Signal Corp"},
        headers={"X-Api-Key": API_KEY},
    )
    r = client.get("/api/v1/assets/NOSIG.SA/signal")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "no_signal_available"


def test_ingestion_creates_signal(client: TestClient) -> None:
    _ingest(client, "SIGN3.SA")
    r = client.get("/api/v1/assets/SIGN3.SA/signal")
    assert r.status_code == 200
    data = r.json()
    assert data["signal_type"] in ("bullish", "bearish", "neutral")
    assert 0.0 <= data["score"] <= 100.0
    assert 0.0 <= data["strength"] <= 1.0
    assert data["strategy_version"] == SCORING_VERSION
    assert isinstance(data["reason_codes"], dict)
    assert isinstance(data["pillar_scores"], dict)
    assert set(data["pillar_scores"].keys()) == {"trend", "momentum", "volume", "risk", "structure"}


def test_signal_has_20_reason_codes(client: TestClient) -> None:
    _ingest(client, "RC20.SA")
    data = client.get("/api/v1/assets/RC20.SA/signal").json()
    assert len(data["reason_codes"]) == 20


def test_ingestion_idempotent_upserts_signal(client: TestClient) -> None:
    df = _minimal_ohlcv(10)
    with patch(
        "app.services.ingestion_service.YFinanceProvider.fetch_ohlcv",
        return_value=df,
    ):
        client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "IDEM2.SA", "days": 30},
            headers={"X-Api-Key": API_KEY},
        )
        client.post(
            "/api/v1/assets/ingestion/run",
            json={"symbol": "IDEM2.SA", "days": 30},
            headers={"X-Api-Key": API_KEY},
        )

    r = client.get("/api/v1/assets/IDEM2.SA/signal")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /assets/{symbol}/signal/recalculate
# ---------------------------------------------------------------------------


def test_recalculate_signal_requires_api_key(client: TestClient) -> None:
    _ingest(client, "RKEY4.SA")
    r = client.post("/api/v1/assets/RKEY4.SA/signal/recalculate")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_recalculate_signal_rejects_wrong_key(client: TestClient) -> None:
    _ingest(client, "BADKEY2.SA")
    r = client.post(
        "/api/v1/assets/BADKEY2.SA/signal/recalculate",
        headers={"X-Api-Key": "wrong"},
    )
    assert r.status_code == 401


def test_recalculate_signal_with_correct_key(client: TestClient) -> None:
    _ingest(client, "CALC3.SA")
    r = client.post(
        "/api/v1/assets/CALC3.SA/signal/recalculate",
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["signal_type"] in ("bullish", "bearish", "neutral")


def test_recalculate_signal_asset_not_found(client: TestClient) -> None:
    r = client.post(
        "/api/v1/assets/GHOST2.SA/signal/recalculate",
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "asset_not_found"


# ---------------------------------------------------------------------------
# GET /rankings
# ---------------------------------------------------------------------------


def test_rankings_empty(client: TestClient) -> None:
    r = client.get("/api/v1/rankings")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["pagination"]["total"] == 0


def test_rankings_returns_assets_with_signals(client: TestClient) -> None:
    _ingest(client, "RANK1.SA")
    _ingest(client, "RANK2.SA")
    r = client.get("/api/v1/rankings")
    assert r.status_code == 200
    data = r.json()["items"]
    assert len(data) == 2
    symbols = {entry["symbol"] for entry in data}
    assert "RANK1.SA" in symbols
    assert "RANK2.SA" in symbols


def test_rankings_ordered_by_score_desc(client: TestClient) -> None:
    _ingest(client, "ORD1.SA")
    _ingest(client, "ORD2.SA")
    data = client.get("/api/v1/rankings").json()["items"]
    scores = [entry["score"] for entry in data]
    assert scores == sorted(scores, reverse=True)


def test_rankings_pagination(client: TestClient) -> None:
    for i in range(3):
        _ingest(client, f"PAG{i}.SA")

    r_all = client.get("/api/v1/rankings?limit=3&offset=0")
    r_page = client.get("/api/v1/rankings?limit=2&offset=1")
    all_data = r_all.json()["items"]
    page_data = r_page.json()["items"]

    assert len(page_data) == 2
    assert page_data[0]["symbol"] == all_data[1]["symbol"]
    assert page_data[1]["symbol"] == all_data[2]["symbol"]


def test_rankings_pagination_meta(client: TestClient) -> None:
    _ingest(client, "META1.SA")
    _ingest(client, "META2.SA")
    r = client.get("/api/v1/rankings?limit=1&offset=0")
    body = r.json()
    assert body["pagination"]["total"] == 2
    assert body["pagination"]["limit"] == 1
    assert body["pagination"]["offset"] == 0
    assert len(body["items"]) == 1


def test_rankings_entry_fields(client: TestClient) -> None:
    _ingest(client, "FLDS.SA")
    entry = client.get("/api/v1/rankings").json()["items"][0]
    assert "asset_id" in entry
    assert "symbol" in entry
    assert "signal_type" in entry
    assert "score" in entry
    assert "strength" in entry
    assert "strategy_version" in entry
    assert "calculated_at" in entry


def test_rankings_filter_by_signal_type(client: TestClient) -> None:
    _ingest(client, "FILT1.SA")
    r = client.get("/api/v1/rankings?signal_type=bullish")
    assert r.status_code == 200
    assert "items" in r.json()


def test_rankings_filter_invalid_signal_type(client: TestClient) -> None:
    r = client.get("/api/v1/rankings?signal_type=unknown")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
