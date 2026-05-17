from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.etl.config import Settings, get_settings


@dataclass(frozen=True)
class TransformResult:
    observations_path: Path
    daily_metrics_path: Path


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _load_raw_record(raw_file: Path) -> dict[str, Any]:
    with raw_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def _series_to_frame(values: list[list[float]], value_column: str) -> pd.DataFrame:
    frame = pd.DataFrame(values, columns=["observed_at_ms", value_column])
    return pd.DataFrame(
        {
            "observed_at": pd.to_datetime(frame["observed_at_ms"], unit="ms", utc=True),
            value_column: frame[value_column],
        }
    )


def build_observations(raw_record: dict[str, Any], settings: Settings) -> pd.DataFrame:
    payload = raw_record.get("payload", raw_record)
    prices = _series_to_frame(payload["prices"], "price_usd")
    market_caps = _series_to_frame(payload["market_caps"], "market_cap_usd")
    volumes = _series_to_frame(payload["total_volumes"], "total_volume_usd")

    merged_observations = prices.merge(market_caps, on="observed_at", how="outer").merge(
        volumes, on="observed_at", how="outer"
    )
    coin_id = raw_record.get("coin_id", settings.coin_id)
    vs_currency = raw_record.get("vs_currency", settings.vs_currency)
    numeric_columns = ["price_usd", "market_cap_usd", "total_volume_usd"]
    observations = pd.DataFrame(
        {
            "coin_id": [coin_id] * len(merged_observations),
            "vs_currency": [vs_currency] * len(merged_observations),
            "observed_at": merged_observations["observed_at"],
            **{
                column: pd.to_numeric(merged_observations[column], errors="coerce")
                for column in numeric_columns
            },
        }
    )

    observations = observations.dropna(subset=["observed_at", "price_usd"])
    filled_metrics = observations[numeric_columns].ffill().bfill()
    observations = pd.DataFrame(
        {
            "coin_id": observations["coin_id"],
            "vs_currency": observations["vs_currency"],
            "observed_at": observations["observed_at"],
            **{column: filled_metrics[column] for column in numeric_columns},
        }
    )
    observations = observations.sort_values(["coin_id", "vs_currency", "observed_at"])
    observations = observations.drop_duplicates(
        subset=["coin_id", "vs_currency", "observed_at"], keep="last"
    )

    return observations[
        [
            "coin_id",
            "vs_currency",
            "observed_at",
            "price_usd",
            "market_cap_usd",
            "total_volume_usd",
        ]
    ]


def build_daily_metrics(observations: pd.DataFrame) -> pd.DataFrame:
    working = pd.DataFrame(
        {
            "coin_id": observations["coin_id"],
            "vs_currency": observations["vs_currency"],
            "metric_date": observations["observed_at"].dt.date,
            "price_usd": observations["price_usd"],
            "market_cap_usd": observations["market_cap_usd"],
            "total_volume_usd": observations["total_volume_usd"],
        }
    )
    daily = (
        working.groupby(["coin_id", "vs_currency", "metric_date"], as_index=False)
        .agg(
            avg_price_usd=("price_usd", "mean"),
            min_price_usd=("price_usd", "min"),
            max_price_usd=("price_usd", "max"),
            avg_market_cap_usd=("market_cap_usd", "mean"),
            total_volume_usd=("total_volume_usd", "sum"),
        )
        .sort_values(["coin_id", "vs_currency", "metric_date"])
    )
    moving_average = daily.groupby(["coin_id", "vs_currency"])[
        "avg_price_usd"
    ].transform(lambda series: series.rolling(window=7, min_periods=1).mean())
    return pd.DataFrame(
        {
            "coin_id": daily["coin_id"],
            "vs_currency": daily["vs_currency"],
            "metric_date": daily["metric_date"],
            "avg_price_usd": daily["avg_price_usd"],
            "min_price_usd": daily["min_price_usd"],
            "max_price_usd": daily["max_price_usd"],
            "avg_market_cap_usd": daily["avg_market_cap_usd"],
            "total_volume_usd": daily["total_volume_usd"],
            "price_7d_moving_avg_usd": moving_average,
        }
    )


def transform(raw_file: Path, settings: Settings | None = None) -> TransformResult:
    active_settings = settings or get_settings()
    active_settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    raw_record = _load_raw_record(raw_file)

    observations = build_observations(raw_record, active_settings)
    daily_metrics = build_daily_metrics(observations)

    timestamp = _utc_timestamp()
    observations_path = active_settings.processed_data_dir / (
        f"crypto_market_observations_{timestamp}.csv.gz"
    )
    daily_metrics_path = active_settings.processed_data_dir / (
        f"daily_crypto_market_metrics_{timestamp}.csv.gz"
    )
    observations.to_csv(observations_path, index=False, compression="gzip")
    daily_metrics.to_csv(daily_metrics_path, index=False, compression="gzip")

    print(f"observations_file={observations_path}")
    print(f"daily_metrics_file={daily_metrics_path}")
    return TransformResult(
        observations_path=observations_path,
        daily_metrics_path=daily_metrics_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform raw CoinGecko JSON into curated compressed CSV files."
    )
    parser.add_argument("--raw-file", required=True, type=Path)
    args = parser.parse_args()
    transform(args.raw_file)


if __name__ == "__main__":
    main()
