"""Popula o banco com ativos de demo e histórico de 1 ano via yfinance."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.session import SessionLocal
from app.services.ingestion_service import ingest_prices

DEMO_ASSETS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "MGLU3.SA",
]


def main() -> None:
    db = SessionLocal()
    try:
        for symbol in DEMO_ASSETS:
            print(f"Ingerindo {symbol}...", end=" ", flush=True)
            result = ingest_prices(db, symbol=symbol, days=365)
            print(f"inseridos={result.inserted}  ignorados={result.skipped}")
    finally:
        db.close()
    print("\nSeed concluído.")


if __name__ == "__main__":
    main()
