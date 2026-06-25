from collections.abc import Generator

import pytest

from app.core.rate_limiter import limiter
from app.db.session import SessionLocal


@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    yield
    db = SessionLocal()
    try:
        db.execute(
            __import__("sqlalchemy").text(
                "TRUNCATE TABLE signals, indicator_snapshots, price_bars, assets"
                " RESTART IDENTITY CASCADE"
            )
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Generator[None, None, None]:
    """Reset in-memory rate limiter storage before each test.

    The limiter singleton persists across test cases; without a reset, tests
    that call the same endpoints repeatedly exhaust the per-minute quota and
    start receiving spurious 429 responses.
    """
    limiter._storage.reset()
    yield
