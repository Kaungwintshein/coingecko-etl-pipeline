from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def extract_raw() -> str:
    from src.etl.extract import extract

    return str(extract())


def transform_raw(**context) -> dict[str, str]:
    from src.etl.transform import transform

    task_instance = context["ti"]
    raw_file = Path(task_instance.xcom_pull(task_ids="extract_task"))
    result = transform(raw_file)
    return {
        "observations_path": str(result.observations_path),
        "daily_metrics_path": str(result.daily_metrics_path),
    }


def load_warehouse(**context) -> None:
    from src.etl.load import load

    task_instance = context["ti"]
    transformed = task_instance.xcom_pull(task_ids="transform_task")
    load(
        Path(transformed["observations_path"]),
        Path(transformed["daily_metrics_path"]),
    )


with DAG(
    dag_id="coingecko_market_pipeline",
    description=(
        "Extract CoinGecko data, curate compressed CSV files, and upsert PostgreSQL facts."
    ),
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["portfolio", "crypto", "etl", "postgres"],
) as dag:
    extract_task = PythonOperator(task_id="extract_task", python_callable=extract_raw)
    transform_task = PythonOperator(
        task_id="transform_task",
        python_callable=transform_raw,
    )
    load_task = PythonOperator(
        task_id="load_task",
        python_callable=load_warehouse,
    )

    extract_task >> transform_task >> load_task
