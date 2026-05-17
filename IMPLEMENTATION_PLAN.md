# Technical Implementation Plan

## Project Choice

Build an end-to-end ETL pipeline using the CoinGecko public API market chart endpoint:

- Source endpoint: `https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart`
- Default entity: Bitcoin priced in USD for the last 30 days
- Raw landing format: timestamped JSON
- Curated format: compressed CSV (`.csv.gz`)
- Warehouse: local PostgreSQL
- Orchestrator: Apache Airflow running in Docker Compose
- Optional infrastructure-as-code: Terraform scaffold for AWS RDS PostgreSQL

This API is suitable for a junior data engineering portfolio because it is public, stable, time-series oriented, and naturally supports analytical modeling such as daily average price and volume metrics.

---

## Phase 1: Local Environment and Repo Setup

### Checklist

- [ ] Initialize Git.
  - Command: `git init`
  - Verify: `git status` shows a clean repository after the first commit.

- [ ] Create a Python virtual environment.
  - Command: `python3 -m venv .venv`
  - Activate: `source .venv/bin/activate`
  - Verify: `which python` points to `.venv/bin/python`.

- [ ] Install pinned dependencies.
  - Command: `pip install --upgrade pip && pip install -r requirements.txt`
  - Libraries used: `requests`, `python-dotenv`, `pandas`, `SQLAlchemy`, `psycopg2-binary`, `tenacity`, `pytest`, `ruff`
  - Verify: `python -c "import requests, pandas, sqlalchemy, psycopg2"` succeeds.

- [ ] Create local environment file.
  - Command: `cp .env.example .env`
  - Verify: `.env` exists and is ignored by Git.

- [ ] Confirm professional ignore rules.
  - File: `.gitignore`
  - Verify: `.env`, `.venv/`, Airflow logs, Terraform state, and generated data zones are not tracked.

---

## Phase 2: Extract - API to Raw Storage

### Script

Create/use: `src/etl/extract.py`

### Responsibilities

- Load runtime config from environment variables via `python-dotenv`.
- Call CoinGecko using `requests.Session`.
- Send an optional API key only from `COINGECKO_API_KEY`.
- Handle:
  - HTTP non-2xx responses
  - `429 Too Many Requests`
  - request timeouts
  - connection failures
  - malformed/empty JSON
- Retry transient failures with exponential backoff using `tenacity`.
- Save the exact raw API response to `data/raw/coingecko_market_chart_<timestamp>.json`.

### Verification

- Command: `python -m src.etl.extract`
- Success criteria:
  - A new JSON file exists under `data/raw/`.
  - File name contains a UTC timestamp.
  - JSON contains `prices`, `market_caps`, and `total_volumes` arrays.
  - Console logs print the raw file path.

---

## Phase 3: Transform - Raw JSON to Curated Analytical Data

### Script

Create/use: `src/etl/transform.py`

### Responsibilities

- Read the latest or supplied raw JSON file.
- Normalize CoinGecko arrays into a tabular dataframe.
- Rename fields to standard `snake_case`:
  - `observed_at`
  - `price_usd`
  - `market_cap_usd`
  - `total_volume_usd`
- Cast explicit datatypes:
  - timestamps to UTC `datetime64[ns, UTC]`
  - numeric metrics to `float64`
  - derived dates to date values
- Handle nulls and invalid values.
- Create an analytical daily aggregation:
  - average daily price
  - minimum daily price
  - maximum daily price
  - average daily market cap
  - total daily volume
  - 7-day moving average price
- Export curated outputs as compressed CSV:
  - `data/processed/crypto_market_observations_<timestamp>.csv.gz`
  - `data/processed/daily_crypto_market_metrics_<timestamp>.csv.gz`

### Verification

- Command: `python -m src.etl.transform --raw-file data/raw/<file>.json`
- Success criteria:
  - compressed CSV files exist in `data/processed/`.
  - Dataframes have no null primary metric timestamps.
  - Numeric columns are numeric, not strings.
  - Aggregated daily table has one row per coin/currency/date.

---

## Phase 4: Load - Curated Data to PostgreSQL Warehouse

### Scripts

Create/use:

- `src/etl/load.py`
- `sql/ddl.sql`

### Target Model

Use a small dimensional model:

- `dim_crypto_asset`
  - `asset_key` primary key
  - `coin_id`
  - `vs_currency`
- `fact_crypto_market_observation`
  - one row per asset and observation timestamp
  - unique key: `(asset_key, observed_at)`
- `fact_daily_crypto_market_metric`
  - one row per asset and metric date
  - unique key: `(asset_key, metric_date)`

### Responsibilities

- Connect through SQLAlchemy using env vars.
- Create schemas/tables if they do not exist.
- Load dimensions first.
- Upsert facts using PostgreSQL `ON CONFLICT DO UPDATE`.
- Avoid destructive table replacement.

### Verification

- Start Postgres: `docker compose up -d postgres`
- Run pipeline: `python -m src.etl.pipeline`
- Verify row counts:
  - `docker compose exec postgres psql -U warehouse_user -d crypto_warehouse -c "select count(*) from fact_crypto_market_observation;"`
  - `docker compose exec postgres psql -U warehouse_user -d crypto_warehouse -c "select count(*) from fact_daily_crypto_market_metric;"`

---

## Phase 5: Automation and Orchestration with Apache Airflow

### Files

Create/use:

- `docker-compose.yml`
- `dags/coingecko_market_pipeline_dag.py`
- `scripts/run_pipeline.sh`

### Responsibilities

- Package the ETL into a repeatable command: `python -m src.etl.pipeline`.
- Run Airflow webserver and scheduler in Docker.
- Schedule the DAG daily.
- Keep tasks separated:
  - extract
  - transform
  - load
- Use Airflow task dependencies and XComs for file paths.
- Mount local project code into Airflow containers.

### Verification

- Initialize and start Airflow: `make up`
- Airflow UI: `http://localhost:8080`
- Default credentials: `airflow` / `airflow`
- Trigger DAG: `coingecko_market_pipeline`
- Success criteria:
  - All DAG tasks turn green.
  - Raw JSON is written.
  - Processed compressed CSV files are written.
  - PostgreSQL facts are populated.

---

## Phase 6: Terraform Infrastructure Scaffold

### Files

Create/use:

- `terraform/aws-rds-postgres/main.tf`
- `terraform/aws-rds-postgres/variables.tf`
- `terraform/aws-rds-postgres/outputs.tf`
- `terraform/aws-rds-postgres/README.md`

### Responsibilities

- Demonstrate infrastructure-as-code thinking.
- Provide an optional AWS RDS PostgreSQL Free Tier-compatible target.
- Keep secrets outside source control through `terraform.tfvars` or environment variables.
- Avoid applying cloud resources by default.

### Verification

- Command: `cd terraform/aws-rds-postgres && terraform init && terraform validate`
- Success criteria:
  - Terraform validates successfully.
  - No secrets are committed.
  - Cloud usage remains explicit and opt-in.

---

## Phase 7: Quality Gates

### Checks

- [ ] `ruff check src tests dags`
- [ ] `pytest -q`
- [ ] `python -m src.etl.pipeline`
- [ ] Airflow DAG runs successfully from the UI.
- [ ] Warehouse row counts are non-zero.
- [ ] Re-running the pipeline does not duplicate rows because upserts are used.

### Portfolio Acceptance Criteria

The project is complete when a reviewer can clone the repo, copy `.env.example` to `.env`, run Docker Compose, trigger the Airflow DAG, and inspect curated data in PostgreSQL without manual code edits.
