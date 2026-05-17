CREATE TABLE IF NOT EXISTS dim_crypto_asset (
    asset_key BIGSERIAL PRIMARY KEY,
    coin_id TEXT NOT NULL,
    vs_currency TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dim_crypto_asset UNIQUE (coin_id, vs_currency)
);

CREATE TABLE IF NOT EXISTS fact_crypto_market_observation (
    asset_key BIGINT NOT NULL REFERENCES dim_crypto_asset(asset_key),
    observed_at TIMESTAMPTZ NOT NULL,
    price_usd NUMERIC(18, 8) NOT NULL,
    market_cap_usd NUMERIC(24, 4),
    total_volume_usd NUMERIC(24, 4),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (asset_key, observed_at)
);

CREATE INDEX IF NOT EXISTS ix_fact_crypto_market_observation_observed_at
    ON fact_crypto_market_observation (observed_at);

CREATE TABLE IF NOT EXISTS fact_daily_crypto_market_metric (
    asset_key BIGINT NOT NULL REFERENCES dim_crypto_asset(asset_key),
    metric_date DATE NOT NULL,
    avg_price_usd NUMERIC(18, 8) NOT NULL,
    min_price_usd NUMERIC(18, 8) NOT NULL,
    max_price_usd NUMERIC(18, 8) NOT NULL,
    avg_market_cap_usd NUMERIC(24, 4),
    total_volume_usd NUMERIC(24, 4),
    price_7d_moving_avg_usd NUMERIC(18, 8),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (asset_key, metric_date)
);

CREATE INDEX IF NOT EXISTS ix_fact_daily_crypto_market_metric_metric_date
    ON fact_daily_crypto_market_metric (metric_date);
