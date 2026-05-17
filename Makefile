.PHONY: setup lint test run up down airflow-init showcase

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

lint:
	. .venv/bin/activate && ruff check src tests dags

test:
	. .venv/bin/activate && pytest -q

run:
	. .venv/bin/activate && python -m src.etl.pipeline

up:
	docker compose up -d postgres airflow-init airflow-webserver airflow-scheduler

down:
	docker compose down

airflow-init:
	docker compose up airflow-init

showcase:
	python3 -m http.server 8000
