from __future__ import annotations

from src.etl.config import get_settings
from src.etl.extract import extract
from src.etl.load import load
from src.etl.transform import transform


def run_pipeline() -> None:
    settings = get_settings()
    raw_file = extract(settings)
    transform_result = transform(raw_file, settings)
    load(transform_result.observations_path, transform_result.daily_metrics_path, settings)


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
