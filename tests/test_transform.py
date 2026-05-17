from __future__ import annotations

from src.etl.config import get_settings
from src.etl.transform import build_daily_metrics, build_observations


def test_build_observations_and_daily_metrics() -> None:
    raw_record = {
        "coin_id": "bitcoin",
        "vs_currency": "usd",
        "payload": {
            "prices": [[1704067200000, 100.0], [1704153600000, 110.0]],
            "market_caps": [[1704067200000, 1000.0], [1704153600000, 1200.0]],
            "total_volumes": [[1704067200000, 50.0], [1704153600000, 60.0]],
        },
    }

    observations = build_observations(raw_record, get_settings())
    daily = build_daily_metrics(observations)

    assert list(observations.columns) == [
        "coin_id",
        "vs_currency",
        "observed_at",
        "price_usd",
        "market_cap_usd",
        "total_volume_usd",
    ]
    assert len(observations) == 2
    assert observations["observed_at"].dt.tz is not None
    assert observations["price_usd"].dtype == "float64"
    assert len(daily) == 2
    assert "price_7d_moving_avg_usd" in daily.columns
    assert daily["avg_price_usd"].iloc[0] == 100.0
