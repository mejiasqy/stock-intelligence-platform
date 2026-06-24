from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    yield
    db = SessionLocal()
    try:
        db.execute(
            __import__("sqlalchemy").text(
                "TRUNCATE TABLE price_bars, assets RESTART IDENTITY CASCADE"
            )
        )
        db.commit()
    finally:
        db.close()
