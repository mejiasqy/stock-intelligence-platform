from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_ready_when_db_unavailable(client: TestClient) -> None:
    with patch("app.api.routers.health.check_connection", return_value=False):
        response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "unavailable"


def test_ready_when_db_connected(client: TestClient) -> None:
    with patch("app.api.routers.health.check_connection", return_value=True):
        response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
