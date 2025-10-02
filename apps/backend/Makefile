.PHONY: help install setup run test lint format clean docker-up docker-down

# Default target
help:
	@echo "🚀 Django Project Commands:"
	@echo ""
	@echo "📦 Setup:"
	@echo "  install     - Install dependencies"
	@echo "  setup       - Full project setup"
	@echo ""
	@echo "🛠 Development:"
	@echo "  run         - Start development server"
	@echo "  shell       - Open Django shell"
	@echo "  migrate     - Run migrations"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test        - Run tests with coverage"
	@echo "  lint        - Run all linting checks"
	@echo "  format      - Format code"
	@echo "  check       - Pre-commit checks"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  docker-logs - View Docker logs"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  clean       - Remove cache files"

# Setup commands
install:
	poetry install

setup: install
	poetry run pre-commit install
	cp .env.example .env
	@echo "✅ Setup complete! Edit .env and run 'make run'"

# Development commands
run:
	cd src && poetry run python manage.py runserver

shell:
	cd src && poetry run python manage.py shell

migrate:
	cd src && poetry run python manage.py migrate

makemigrations:
	cd src && poetry run python manage.py makemigrations

superuser:
	cd src && poetry run python manage.py createsuperuser

collectstatic:
	cd src && poetry run python manage.py collectstatic --noinput

# Testing and quality
test:
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

test-fast:
	poetry run pytest -x -v

lint:
	poetry run ruff check
	poetry run mypy src/

format:
	poetry run ruff format
	poetry run ruff check --fix

check:
	poetry run pre-commit run --all-files

# Docker commands
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec app bash

# Celery commands
celery-worker:
	cd src && poetry run celery -A config worker --loglevel=info

celery-beat:
	cd src && poetry run celery -A config beat --loglevel=info

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
