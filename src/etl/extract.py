from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from requests import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.etl.config import Settings, get_settings


class RetryableApiError(RuntimeError):
    pass


class FatalApiError(RuntimeError):
    pass


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _validate_response(response: Response) -> None:
    if response.status_code == 429 or response.status_code >= 500:
        raise RetryableApiError(
            f"CoinGecko returned retryable status {response.status_code}: {response.text[:300]}"
        )
    if response.status_code >= 400:
        raise FatalApiError(
            f"CoinGecko returned fatal status {response.status_code}: {response.text[:300]}"
        )


@retry(
    retry=retry_if_exception_type((RetryableApiError, requests.RequestException)),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    stop=stop_after_attempt(4),
    reraise=True,
)
def fetch_market_chart(settings: Settings) -> dict[str, Any]:
    url = f"https://api.coingecko.com/api/v3/coins/{settings.coin_id}/market_chart"
    params = {"vs_currency": settings.vs_currency, "days": settings.market_chart_days}

    with requests.Session() as session:
        response = session.get(
            url,
            params=params,
            headers=settings.api_headers,
            timeout=settings.api_timeout_seconds,
        )
        _validate_response(response)
        try:
            payload = response.json()
        except ValueError as exc:
            raise FatalApiError("CoinGecko response was not valid JSON") from exc

    required_arrays = {"prices", "market_caps", "total_volumes"}
    missing_arrays = required_arrays.difference(payload)
    if missing_arrays:
        raise FatalApiError(f"CoinGecko payload missing required arrays: {sorted(missing_arrays)}")

    return payload


def save_raw_payload(payload: dict[str, Any], settings: Settings) -> Path:
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(UTC).isoformat()
    raw_record = {
        "source": "coingecko",
        "endpoint": "/api/v3/coins/{coin_id}/market_chart",
        "coin_id": settings.coin_id,
        "vs_currency": settings.vs_currency,
        "market_chart_days": settings.market_chart_days,
        "fetched_at_utc": fetched_at,
        "payload": payload,
    }
    output_path = settings.raw_data_dir / f"coingecko_market_chart_{_utc_timestamp()}.json"
    output_path.write_text(json.dumps(raw_record, indent=2), encoding="utf-8")
    return output_path


def extract(settings: Settings | None = None) -> Path:
    active_settings = settings or get_settings()
    payload = fetch_market_chart(active_settings)
    output_path = save_raw_payload(payload, active_settings)
    print(f"raw_file={output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CoinGecko market chart data to raw JSON.")
    parser.parse_args()
    extract()


if __name__ == "__main__":
    main()
