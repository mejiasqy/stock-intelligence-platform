from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limiter import limiter
from app.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Generator[None, None, None]:
    """Reset in-memory rate limiter storage before each test."""
    limiter._storage.reset()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
