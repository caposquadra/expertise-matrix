# Матрица компетенций департамента тестирования

Internal web portal for managing a testing team's competency matrix. Employees self-assess skills, managers calibrate, and admins manage the whole process with review cycles and individual development plans (IDP).

## Stack

- **Backend:** Python 3.12, FastAPI, async SQLAlchemy 2.0 + asyncpg, PostgreSQL 15
- **Frontend:** React 19, TypeScript, Vite, Mantine 7, Recharts, Axios, Zustand
- **Infra:** Docker Compose (Postgres + Backend + Nginx), GitHub Actions CI

## Quick Start

```bash
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
docker compose -f docker/docker-compose.yml exec backend python -m scripts.seed
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8080/api/v1
- **API Docs:** http://localhost:8080/docs

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

## Features

- **Skill matrix** — grid view of all employees × skills with color-coded levels (1–3), grouped by category
- **Self-assessment** — employees rate their own skills; managers override/calibrate
- **Review cycles** — periodic structured reviews with expert and manager evaluation rounds
- **IDP plans** — individual development plans with goals, target levels, and deadlines
- **Dashboard** — employee count, skill coverage, weakest skills, promotion-ready candidates
- **Reports & analytics** — team summary, growth zones (self vs manager gap), CSV/Excel export
- **History** — full audit trail of level changes
- **Admin panel** — manage users, skills, teams, and system settings

## Role-based access

| Role | Capabilities |
|---|---|
| **Admin** | Full access — manage users, skills, teams; edit any assessment; export data |
| **Manager** | View team matrix; edit self & employee assessments; create IDPs; manage review cycles |
| **Expert** | Evaluate specific skills during review cycles (expert level) |
| **Employee** | View own profile; self-assess within review cycles; view own IDP |

## Authentication

JWT-based with **access token (30 min)** in `Authorization: Bearer` header and **refresh token (7 days)** in HTTP-only cookie. On 401 the frontend interceptor automatically attempts a silent refresh.

## Tests

| Suite | Count | Command |
|---|---|---|
| Backend integration | 121 | `make test-backend` |
| Frontend unit | 11 | `npm test` (in `frontend/`) |
| E2E (Playwright) | 5 smoke | `npx playwright test` (in `frontend/`) |

```bash
make test-backend       # Run all backend tests
make test-frontend      # Run frontend unit tests
make test-e2e           # Run Playwright E2E tests
```

## Commands

```bash
make up                 # Start all services
make down               # Stop all services
make restart            # Restart containers
make logs               # Follow container logs
make migrate            # alembic upgrade head
make makemigrations name="desc"  # Create new migration
make seed               # Seed test data
make test-backend       # Backend integration tests (121)
make test-frontend      # Frontend vitest unit tests
make test-e2e           # Playwright E2E tests
make test-all           # Backend + Frontend
make lint               # ruff check + eslint + mypy + tsc
make shell-db           # psql into the database
make shell-backend      # bash into backend container
```

## Project Structure

```
backend/                  FastAPI application
  app/
    api/v1/               API routers
      auth.py             Login, register, refresh, logout
      assessments.py      Skill assessments CRUD
      employees.py        Employee management
      skills.py           Skill catalog
      teams.py            Team management
      reviews.py          Review cycles
      ipr.py              IDP plans and goals
      reports.py          Dashboard and analytics
      export.py           CSV / Excel export
      constants.py        Grade targets, enums
    core/
      config.py           Pydantic settings
      database.py         Async engine + session factory
      security.py         JWT creation/verification, password hashing
    models/               SQLAlchemy models
    schemas/              Pydantic request/response schemas
  alembic/                DB migrations (7 revisions)
  scripts/
    seed.py               Seed test data
    backfill_assessments.py  One-time default assessment backfill
  tests/                  Integration tests (121)
frontend/                 React SPA
  src/
    pages/                Page components
    components/           Reusable components (SkillLevelEditor, ProtectedRoute, Layout)
    api/client.ts         Axios client with JWT interceptor + silent refresh
    store/auth.ts         Zustand auth store
  e2e/                    Playwright smoke tests
docker/                   Docker Compose + Dockerfiles
.github/workflows/        CI pipelines
```

## Key design decisions

- **Skill scale 1–3** (no level 4/5) — simplified to match the team's actual grading model
- **Assessments auto-filled on registration** — new employees get `GRADE_TARGETS[grade]` for every active skill
- **Only managers edit outside review cycles** — employees can only modify assessments during an active review; otherwise 403
- **Refresh token in cookie** — HTTP-only, path-scoped to `/api/v1/auth`, reducing XSS surface vs body response
- **No rate limiter** — removed `slowapi` to eliminate test flakiness; login has no throttling
- **Pagination** — all list endpoints use `skip`/`limit` with sensible defaults (200–500)
