from collections.abc import Generator

import pytest

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
