from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    coingecko_api_key: str | None
    coin_id: str
    vs_currency: str
    market_chart_days: int
    api_timeout_seconds: int
    raw_data_dir: Path
    processed_data_dir: Path
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg2://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def api_headers(self) -> dict[str, str]:
        if not self.coingecko_api_key:
            return {}
        return {"x-cg-demo-api-key": self.coingecko_api_key}


def get_settings() -> Settings:
    return Settings(
        coingecko_api_key=os.getenv("COINGECKO_API_KEY") or None,
        coin_id=os.getenv("COIN_ID", "bitcoin"),
        vs_currency=os.getenv("VS_CURRENCY", "usd"),
        market_chart_days=int(os.getenv("MARKET_CHART_DAYS", "30")),
        api_timeout_seconds=int(os.getenv("API_TIMEOUT_SECONDS", "30")),
        raw_data_dir=Path(os.getenv("RAW_DATA_DIR", "data/raw")),
        processed_data_dir=Path(os.getenv("PROCESSED_DATA_DIR", "data/processed")),
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_db=os.getenv("POSTGRES_DB", "crypto_warehouse"),
        postgres_user=os.getenv("POSTGRES_USER", "warehouse_user"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "warehouse_password"),
    )
