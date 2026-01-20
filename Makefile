.PHONY: help setup install clean test lint format docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make setup          - Initial project setup"
	@echo "  make install        - Install dependencies"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker services"
	@echo "  make docker-down    - Stop Docker services"
	@echo "  make migrate        - Run database migrations"
	@echo "  make train          - Train ML models"
	@echo "  make backtest       - Run backtest"

setup:
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements/dev.txt
	cp .env.example .env
	@echo "Setup complete! Edit .env with your configuration."

install:
	pip install -r requirements/dev.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist .pytest_cache .coverage htmlcov

test:
	pytest tests/ -v --cov=src --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	flake8 src tests
	pylint src
	mypy src

format:
	black src tests
	isort src tests

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

train:
	python scripts/train_models.py

backtest:
	python scripts/backtest_strategy.py

data-download:
	python scripts/download_historical_data.py

notebook:
	jupyter lab notebooks/

run-backend:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm start
