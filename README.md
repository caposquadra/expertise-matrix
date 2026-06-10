# Expertise Matrix

Internal web portal for managing a testing team's competency matrix.

## Stack

- **Backend:** Python FastAPI + async SQLAlchemy + PostgreSQL
- **Frontend:** React 19 + Vite + Mantine 7 + Recharts
- **Infra:** Docker Compose (Postgres + Backend + Nginx)

## Quick Start

```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d --build

# Apply migrations
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head

# Seed test data
docker compose -f docker/docker-compose.yml exec backend python -m scripts.seed
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8080/api/v1
- Health: http://localhost:8080/health

## Users (seeded)

| Email | Password | Role |
|---|---|---|
| admin@example.com | admin123 | admin |
| manager@example.com | manager123 | manager |
| expert@example.com | expert123 | expert |
| ivan@example.com | ivan123 | employee |
| petr@example.com | petr123 | employee |
| anna@example.com | anna123 | employee |
| olga@example.com | olga123 | employee |
| dmitry@example.com | dmitry123 | employee |

## Tests

```bash
make test-backend
```

Runs 53 integration tests against an isolated `expertise_matrix_test` database.

## Commands

```bash
make test-backend   # Run backend tests
```

## Project Structure

```
backend/            FastAPI application
  app/api/v1/       API routers (auth, skills, assessments, employees, ipr, reports, export, reviews)
  app/core/         Config, DB, security
  app/models/       SQLAlchemy models (9 tables)
  app/schemas/      Pydantic request/response schemas
  alembic/          DB migrations
  tests/            Integration tests (53)
frontend/           React SPA
  src/pages/        9 page components
  src/components/   Layout, ProtectedRoute
  src/api/          Axios client + JWT interceptor
  src/store/        Zustand auth store
docker/             Docker Compose + Dockerfiles
```
