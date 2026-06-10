.PHONY: up down build migrate test lint coverage precommit ci

up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

build:
	docker compose -f docker/docker-compose.yml build

logs:
	docker compose -f docker/docker-compose.yml logs -f

restart:
	docker compose -f docker/docker-compose.yml restart

ps:
	docker compose -f docker/docker-compose.yml ps

migrate:
	docker compose -f docker/docker-compose.yml exec backend alembic upgrade head

makemigrations:
	docker compose -f docker/docker-compose.yml exec backend alembic revision --autogenerate -m "$(name)"

seed:
	docker compose -f docker/docker-compose.yml exec backend python -m scripts.seed

shell-backend:
	docker compose -f docker/docker-compose.yml exec backend /bin/bash

shell-db:
	docker compose -f docker/docker-compose.yml exec postgres psql -U app -d expertise_matrix

# === Tests ===

test-backend:
	docker compose -f docker/docker-compose.yml exec -e DATABASE_URL=postgresql+asyncpg://app:app_secret@postgres:5432/expertise_matrix_test backend python -m pytest tests/ -v --ignore=tests/unit/test_contract.py

test-backend-coverage:
	docker compose -f docker/docker-compose.yml exec -e DATABASE_URL=postgresql+asyncpg://app:app_secret@postgres:5432/expertise_matrix_test backend python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

test-backend-unit:
	docker compose -f docker/docker-compose.yml exec -e DATABASE_URL=postgresql+asyncpg://app:app_secret@postgres:5432/expertise_matrix_test backend python -m pytest tests/unit/ -v

test-backend-integration:
	docker compose -f docker/docker-compose.yml exec -e DATABASE_URL=postgresql+asyncpg://app:app_secret@postgres:5432/expertise_matrix_test backend python -m pytest tests/ -v -m "not unit"

test-frontend:
	docker compose -f docker/docker-compose.yml run --rm frontend-ci sh -c "npm install && npm test"

test-frontend-coverage:
	docker compose -f docker/docker-compose.yml run --rm frontend-ci sh -c "npm install && npm test -- --coverage"

test-all: test-backend test-frontend

coverage: test-backend-coverage test-frontend-coverage

# === Lint ===

lint-backend:
	docker compose -f docker/docker-compose.yml exec backend sh -c "ruff check app/ && ruff format --check app/"

lint-frontend:
	docker compose -f docker/docker-compose.yml run --rm frontend-ci sh -c "npm install && npm run lint"

typecheck-backend:
	docker compose -f docker/docker-compose.yml exec backend mypy app/ --ignore-missing-imports

typecheck-frontend:
	docker compose -f docker/docker-compose.yml run --rm frontend-ci sh -c "npm install && npx tsc --noEmit"

lint: lint-backend lint-frontend typecheck-backend typecheck-frontend

# === CI (local) ===

precommit:
	docker compose -f docker/docker-compose.yml run --rm frontend-ci sh -c "npm install" && docker compose -f docker/docker-compose.yml exec backend pre-commit run --all-files

ci: lint test-all typecheck-backend typecheck-frontend

test-all-fast:
	docker compose -f docker/docker-compose.yml exec -e DATABASE_URL=postgresql+asyncpg://app:app_secret@postgres:5432/expertise_matrix_test backend python -m pytest tests/ -v -x -n auto

# === E2E ===

test-e2e:
	docker compose -f docker/docker-compose.yml run --rm frontend-ci sh -c "npm install && npx playwright test"

# === Performance ===

test-performance:
	docker compose -f docker/docker-compose.yml exec backend locust -f tests/performance/locustfile.py --headless -u 10 -r 2 --run-time 30s --host http://backend:8000

test-contract:
	docker compose -f docker/docker-compose.yml exec -e DATABASE_URL=postgresql+asyncpg://app:app_secret@postgres:5432/expertise_matrix_test backend python -m pytest tests/unit/test_contract.py -v --maxfail=1
