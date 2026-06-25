"""Testes de contrato transversais: envelope de erro, autenticação, paginação, CORS e rate limit."""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limiter import limiter

API_KEY = settings.api_secret_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_error_envelope(body: dict, expected_code: str | None = None) -> None:
    assert "error" in body, f"Resposta sem campo 'error': {body}"
    err = body["error"]
    assert "code" in err, f"'error' sem campo 'code': {err}"
    assert "message" in err, f"'error' sem campo 'message': {err}"
    assert "request_id" in err, f"'error' sem campo 'request_id': {err}"
    if expected_code:
        assert err["code"] == expected_code, f"Esperado code={expected_code}, obtido {err['code']}"


def _assert_paginated(body: dict) -> None:
    assert "items" in body, f"Resposta sem 'items': {body}"
    assert "pagination" in body, f"Resposta sem 'pagination': {body}"
    pag = body["pagination"]
    assert "limit" in pag
    assert "offset" in pag
    assert "total" in pag


# ---------------------------------------------------------------------------
# Envelope de erro padronizado
# ---------------------------------------------------------------------------


def test_404_returns_error_envelope(client: TestClient) -> None:
    r = client.get("/api/v1/assets/NOSUCHSYMBOL.SA/analysis")
    assert r.status_code == 404
    _assert_error_envelope(r.json(), "asset_not_found")


def test_401_returns_error_envelope(client: TestClient) -> None:
    r = client.post("/api/v1/assets/ingestion/run", json={"symbol": "X.SA", "days": 10})
    assert r.status_code == 401
    _assert_error_envelope(r.json(), "unauthorized")


def test_403_wrong_key_returns_error_envelope(client: TestClient) -> None:
    r = client.post(
        "/api/v1/assets/ingestion/run",
        json={"symbol": "X.SA", "days": 10},
        headers={"X-Api-Key": "definitely-wrong-key"},
    )
    assert r.status_code == 401
    _assert_error_envelope(r.json(), "unauthorized")


def test_422_query_validation_returns_error_envelope(client: TestClient) -> None:
    r = client.get("/api/v1/assets?limit=0")
    assert r.status_code == 422
    _assert_error_envelope(r.json(), "validation_error")
    assert "fields" in r.json()["error"]


def test_422_body_validation_returns_error_envelope(client: TestClient) -> None:
    r = client.post(
        "/api/v1/backtests/run",
        json={"symbol": "X.SA", "initial_capital": -1},
        headers={"X-Api-Key": API_KEY},
    )
    assert r.status_code == 422
    _assert_error_envelope(r.json(), "validation_error")


def test_422_fields_are_safe(client: TestClient) -> None:
    """fields list must not expose internal stack traces or SQL."""
    r = client.get("/api/v1/assets?limit=0")
    fields = r.json()["error"].get("fields", [])
    for field in fields:
        msg = json.dumps(field).lower()
        assert "traceback" not in msg
        assert "sqlalchemy" not in msg


def test_error_message_does_not_expose_internals(client: TestClient) -> None:
    r = client.get("/api/v1/assets/NOSUCHSYMBOL.SA/analysis")
    message = r.json()["error"]["message"]
    assert "traceback" not in message.lower()
    assert "sqlalchemy" not in message.lower()
    assert "postgresql" not in message.lower()


# ---------------------------------------------------------------------------
# 429 — Rate limit exceeded
# ---------------------------------------------------------------------------


def test_429_returns_error_envelope(client: TestClient) -> None:
    """Verify RateLimitExceeded maps to the standard error envelope.

    Since rate limits are per-IP and use minute windows (120+/minute by
    default), they cannot be reached in a normal test run. This test patches
    the limiter's internal check to simulate the condition deterministically.
    RateLimitExceeded expects a slowapi.wrappers.Limit; we use MagicMock to
    satisfy its attribute access pattern without constructing the full object.
    """
    fake_limit = MagicMock()
    fake_limit.error_message = None
    fake_limit.limit.__str__ = lambda self: "1 per 1 minute"

    def _always_exceeded(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RateLimitExceeded(fake_limit)

    with patch.object(limiter, "_check_request_limit", side_effect=_always_exceeded):
        r = client.get("/api/v1/assets")

    assert r.status_code == 429
    _assert_error_envelope(r.json(), "rate_limit_exceeded")
    assert "retry-after" in r.headers


# ---------------------------------------------------------------------------
# X-Request-ID propagado na resposta
# ---------------------------------------------------------------------------


def test_request_id_echoed_in_response(client: TestClient) -> None:
    r = client.get("/api/v1/assets", headers={"X-Request-ID": "test-req-123"})
    assert r.headers.get("x-request-id") == "test-req-123"


def test_request_id_generated_when_absent(client: TestClient) -> None:
    r = client.get("/api/v1/assets")
    assert r.headers.get("x-request-id") is not None
    assert len(r.headers["x-request-id"]) > 0


def test_request_id_in_error_body(client: TestClient) -> None:
    r = client.get("/api/v1/assets/NOSUCH.SA/analysis", headers={"X-Request-ID": "err-id-456"})
    assert r.json()["error"]["request_id"] == "err-id-456"


def test_request_id_present_in_success_response(client: TestClient) -> None:
    r = client.get("/api/v1/assets", headers={"X-Request-ID": "success-req-789"})
    assert r.status_code == 200
    assert r.headers.get("x-request-id") == "success-req-789"


# ---------------------------------------------------------------------------
# Paginação padronizada
# ---------------------------------------------------------------------------


def test_assets_list_paginated(client: TestClient) -> None:
    r = client.get("/api/v1/assets")
    assert r.status_code == 200
    _assert_paginated(r.json())


def test_rankings_paginated(client: TestClient) -> None:
    r = client.get("/api/v1/rankings")
    assert r.status_code == 200
    _assert_paginated(r.json())


def test_backtests_list_paginated(client: TestClient) -> None:
    r = client.get("/api/v1/backtests")
    assert r.status_code == 200
    _assert_paginated(r.json())


def test_backtests_list_has_correct_empty_state(client: TestClient) -> None:
    r = client.get("/api/v1/backtests")
    body = r.json()
    assert body["items"] == []
    assert body["pagination"]["total"] == 0
    assert body["pagination"]["limit"] == 50
    assert body["pagination"]["offset"] == 0


# ---------------------------------------------------------------------------
# Validação de limites de paginação
# ---------------------------------------------------------------------------


def test_pagination_limit_zero_returns_422(client: TestClient) -> None:
    r = client.get("/api/v1/assets?limit=0")
    assert r.status_code == 422
    _assert_error_envelope(r.json(), "validation_error")


def test_pagination_limit_too_high_returns_422(client: TestClient) -> None:
    r = client.get("/api/v1/assets?limit=101")
    assert r.status_code == 422
    _assert_error_envelope(r.json(), "validation_error")


def test_pagination_offset_negative_returns_422(client: TestClient) -> None:
    r = client.get("/api/v1/rankings?offset=-1")
    assert r.status_code == 422
    _assert_error_envelope(r.json(), "validation_error")


def test_trades_pagination_limit_above_max_500_returns_422(client: TestClient) -> None:
    """Trades endpoint allows up to 500 per page; 501 must be rejected."""
    r = client.get("/api/v1/backtests/1/trades?limit=501")
    assert r.status_code == 422
    _assert_error_envelope(r.json(), "validation_error")


def test_trades_pagination_limit_500_is_accepted(client: TestClient) -> None:
    """Limit of 500 is the maximum allowed for trades; must not return 422.
    A 404 is expected because backtest run 1 does not exist."""
    r = client.get("/api/v1/backtests/1/trades?limit=500")
    assert r.status_code == 404
    _assert_error_envelope(r.json(), "backtest_run_not_found")


# ---------------------------------------------------------------------------
# Proteção de endpoints mutáveis
# ---------------------------------------------------------------------------


def test_all_write_endpoints_require_api_key(client: TestClient) -> None:
    write_endpoints = [
        ("/api/v1/assets", "post", {"symbol": "X.SA", "name": "X"}),
        ("/api/v1/assets/ingestion/run", "post", {"symbol": "X.SA", "days": 10}),
        ("/api/v1/assets/X.SA/analysis/recalculate", "post", {}),
        ("/api/v1/assets/X.SA/signal/recalculate", "post", {}),
        ("/api/v1/backtests/run", "post", {"symbol": "X.SA"}),
    ]
    for path, method, body in write_endpoints:
        r = getattr(client, method)(path, json=body)
        assert r.status_code == 401, (
            f"{method.upper()} {path} should return 401, got {r.status_code}"
        )
        assert r.json()["error"]["code"] == "unauthorized"


def test_read_endpoints_do_not_require_api_key(client: TestClient) -> None:
    """Read-only endpoints must be accessible without authentication."""
    read_endpoints = [
        "/api/v1/assets",
        "/api/v1/rankings",
        "/api/v1/backtests",
        "/api/v1/health",
    ]
    for path in read_endpoints:
        r = client.get(path)
        assert r.status_code != 401, f"GET {path} should not require API key, got 401"


# ---------------------------------------------------------------------------
# CORS / preflight
# ---------------------------------------------------------------------------


def test_cors_preflight_allowed_origin(client: TestClient) -> None:
    """OPTIONS preflight from allowed origin must return 200 with CORS headers."""
    r = client.options(
        "/api/v1/assets",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert r.status_code == 200
    assert "access-control-allow-origin" in r.headers


def test_cors_allow_credentials_is_false(client: TestClient) -> None:
    """The API must not set allow-credentials to true (no session cookies)."""
    r = client.get("/api/v1/assets", headers={"Origin": "http://localhost:3000"})
    assert r.headers.get("access-control-allow-credentials", "false").lower() != "true"
