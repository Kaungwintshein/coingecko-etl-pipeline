from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from src.etl.config import Settings, get_settings

DDL_PATH = Path(__file__).resolve().parents[2] / "sql" / "ddl.sql"


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def apply_ddl(engine: Engine) -> None:
    ddl = DDL_PATH.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.execute(text(ddl))


def _records_from_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    cleaned = frame.where(pd.notnull(frame), None)
    return cleaned.to_dict(orient="records")


def upsert_asset(engine: Engine, coin_id: str, vs_currency: str) -> int:
    metadata = MetaData()
    asset_table = Table("dim_crypto_asset", metadata, autoload_with=engine)
    statement = (
        insert(asset_table)
        .values(coin_id=coin_id, vs_currency=vs_currency)
        .on_conflict_do_update(
            constraint="uq_dim_crypto_asset",
            set_={"updated_at": text("NOW()")},
        )
        .returning(asset_table.c.asset_key)
    )
    with engine.begin() as connection:
        return int(connection.execute(statement).scalar_one())


def upsert_observations(engine: Engine, observations: pd.DataFrame, asset_key: int) -> int:
    metadata = MetaData()
    table = Table("fact_crypto_market_observation", metadata, autoload_with=engine)
    load_frame = observations.copy()
    load_frame["asset_key"] = asset_key
    load_frame = load_frame[
        ["asset_key", "observed_at", "price_usd", "market_cap_usd", "total_volume_usd"]
    ]
    records = _records_from_frame(load_frame)
    if not records:
        return 0

    statement = insert(table).values(records)
    update_columns = {
        "price_usd": statement.excluded.price_usd,
        "market_cap_usd": statement.excluded.market_cap_usd,
        "total_volume_usd": statement.excluded.total_volume_usd,
        "loaded_at": text("NOW()"),
    }
    statement = statement.on_conflict_do_update(
        index_elements=["asset_key", "observed_at"], set_=update_columns
    )
    with engine.begin() as connection:
        result = connection.execute(statement)
    return int(result.rowcount or 0)


def upsert_daily_metrics(engine: Engine, daily_metrics: pd.DataFrame, asset_key: int) -> int:
    metadata = MetaData()
    table = Table("fact_daily_crypto_market_metric", metadata, autoload_with=engine)
    load_frame = daily_metrics.copy()
    load_frame["asset_key"] = asset_key
    load_frame = load_frame[
        [
            "asset_key",
            "metric_date",
            "avg_price_usd",
            "min_price_usd",
            "max_price_usd",
            "avg_market_cap_usd",
            "total_volume_usd",
            "price_7d_moving_avg_usd",
        ]
    ]
    records = _records_from_frame(load_frame)
    if not records:
        return 0

    statement = insert(table).values(records)
    update_columns = {
        "avg_price_usd": statement.excluded.avg_price_usd,
        "min_price_usd": statement.excluded.min_price_usd,
        "max_price_usd": statement.excluded.max_price_usd,
        "avg_market_cap_usd": statement.excluded.avg_market_cap_usd,
        "total_volume_usd": statement.excluded.total_volume_usd,
        "price_7d_moving_avg_usd": statement.excluded.price_7d_moving_avg_usd,
        "loaded_at": text("NOW()"),
    }
    statement = statement.on_conflict_do_update(
        index_elements=["asset_key", "metric_date"], set_=update_columns
    )
    with engine.begin() as connection:
        result = connection.execute(statement)
    return int(result.rowcount or 0)


def read_curated_files(
    observations_file: Path,
    daily_metrics_file: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    observations = pd.read_csv(observations_file, parse_dates=["observed_at"])
    raw_daily_metrics = pd.read_csv(daily_metrics_file, parse_dates=["metric_date"])
    daily_metrics = raw_daily_metrics.assign(
        metric_date=raw_daily_metrics["metric_date"].dt.date
    )
    return observations, daily_metrics


def load(
    observations_file: Path,
    daily_metrics_file: Path,
    settings: Settings | None = None,
) -> None:
    active_settings = settings or get_settings()
    engine = create_db_engine(active_settings)
    apply_ddl(engine)

    observations, daily_metrics = read_curated_files(observations_file, daily_metrics_file)
    if observations.empty:
        raise ValueError("Observations curated file is empty; refusing to load warehouse tables")

    coin_id = str(observations["coin_id"].iloc[0])
    vs_currency = str(observations["vs_currency"].iloc[0])
    asset_key = upsert_asset(engine, coin_id=coin_id, vs_currency=vs_currency)
    observation_count = upsert_observations(engine, observations, asset_key)
    daily_count = upsert_daily_metrics(engine, daily_metrics, asset_key)

    print(f"asset_key={asset_key}")
    print(f"observation_rows_upserted={observation_count}")
    print(f"daily_metric_rows_upserted={daily_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load curated CoinGecko data into PostgreSQL.")
    parser.add_argument("--observations-file", required=True, type=Path)
    parser.add_argument("--daily-metrics-file", required=True, type=Path)
    args = parser.parse_args()
    load(args.observations_file, args.daily_metrics_file)


if __name__ == "__main__":
    main()
