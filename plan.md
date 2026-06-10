# План разработки портала матрицы экспертизы тестировщиков

---

## Содержание

1. [Анализ требований и проектирование](#1-анализ-требований-и-проектирование)
2. [Архитектура и технологии](#2-архитектура-и-технологии)
3. [Настройка окружения и инфраструктуры](#3-настройка-окружения-и-инфраструктуры)
4. [Разработка бэкенда](#4-разработка-бэкенда)
5. [Разработка фронтенда](#5-разработка-фронтенда)
6. [Интеграция и тестирование](#6-интеграция-и-тестирование)
7. [Документация и развёртывание](#7-документация-и-развёртывание)
8. [Риски и компромиссы](#8-риски-и-компромиссы)
9. [MVP: первые 2 недели](#9-mvp-первые-2-недели)
10. [Расширения после MVP](#10-расширения-после-mvp)

---

## 1. Анализ требований и проектирование

**Оценка: 2 дня**

### 1.1 Категории навыков (25+ компетенций)

| Категория | Навыки |
|-----------|--------|
| **ОС и инфраструктура** | Linux (администрирование), работа с сетями, Docker / контейнеризация, Kubernetes (базовый), настройка CI/CD (GitLab CI / Jenkins / GitHub Actions) |
| **Базы данных** | SQL (сложные запросы, оптимизация), PostgreSQL, работа с NoSQL (Redis, MongoDB — ознакомительно) |
| **Тестирование API** | REST API (Postman / curl), GraphQL, gRPC, нагрузочное тестирование (JMeter / k6 / Locust) |
| **Тестирование UI** | Selenium / Playwright / Cypress, верстка (HTML/CSS basics), кроссбраузерное тестирование, accessibility testing |
| **Автоматизация** | Фреймворки (pytest / PyTest + Selenium / Playwright), Page Object Model, написание кастомных утилит, работа с отчётами (Allure) |
| **TMS и процессы** | TestRail / Zephyr / Allure TestOps, баг-трекинг (Jira / YouTrack), тест-дизайн (эквивалентность, граничные значения, попарное тестирование) |
| **Программирование** | Python (автотесты, скрипты), TypeScript/JavaScript (базовый), bash-скриптинг |
| **Софт-скиллы** | Наставничество, планирование (оценка задач в сторипоинтах/часах), проведение код-ревью автотестов, коммуникация с командой |

### 1.2 Роли и права доступа

| Роль | Права |
|------|-------|
| **Admin** | Полный доступ: управление пользователями (создание, блокировка, смена роли), редактирование списка навыков, просмотр всех профилей и матрицы, редактирование любых оценок, экспорт |
| **Руководитель** (Head / TL) | Просмотр матрицы всей команды, редактирование оценок (своих подчинённых), создание ИПР, просмотр истории, экспорт |
| **Сотрудник** | Просмотр **только своего** профиля и оценок, самооценка (заполнение своей строки), просмотр своего ИПР |

### 1.3 Схема базы данных

```
employees
---------
id              UUID  PK
email           VARCHAR(255)  UNIQUE, NOT NULL
password_hash   VARCHAR(255)  NOT NULL
full_name       VARCHAR(255)  NOT NULL
role            ENUM('admin', 'manager', 'employee')  NOT NULL
grade           ENUM('junior', 'middle', 'senior')     -- общий грейд сотрудника
team_id         UUID  FK -> teams.id  (nullable)
is_active       BOOLEAN  DEFAULT true
created_at      TIMESTAMP
updated_at      TIMESTAMP

teams
-----
id              UUID  PK
name            VARCHAR(255)  NOT NULL
description     TEXT

skills
------
id              UUID  PK
name            VARCHAR(255)  NOT NULL
category        VARCHAR(100)  NOT NULL        -- например 'linux', 'sql', 'automation'
description     TEXT
sort_order      INTEGER  DEFAULT 0
is_active       BOOLEAN  DEFAULT true
created_at      TIMESTAMP

assessments
-----------
id              UUID  PK
employee_id     UUID  FK -> employees.id  ON DELETE CASCADE
skill_id        UUID  FK -> skills.id     ON DELETE CASCADE
self_level      INTEGER  CHECK(1..5)             -- самооценка (1-5)
manager_level   INTEGER  CHECK(1..5)             -- оценка руководителя (1-5)
target_level    INTEGER  CHECK(1..5)             -- целевой уровень (для ИПР)
updated_by      UUID  FK -> employees.id
created_at      TIMESTAMP
updated_at      TIMESTAMP

UNIQUE(employee_id, skill_id)

assessment_history
------------------
id              UUID  PK
assessment_id   UUID  FK -> assessments.id  ON DELETE CASCADE
field_name      VARCHAR(50)   -- 'self_level' | 'manager_level' | 'target_level'
old_value       INTEGER
new_value       INTEGER
changed_by      UUID  FK -> employees.id
changed_at      TIMESTAMP

ipr_plans
---------
id              UUID  PK
employee_id     UUID  FK -> employees.id  ON DELETE CASCADE
title           VARCHAR(255)  NOT NULL
description     TEXT
status          ENUM('draft', 'active', 'completed', 'cancelled')  DEFAULT 'draft'
created_by      UUID  FK -> employees.id
created_at      TIMESTAMP
updated_at      TIMESTAMP

ipr_goals
---------
id              UUID  PK
ipr_plan_id     UUID  FK -> ipr_plans.id  ON DELETE CASCADE
skill_id        UUID  FK -> skills.id
current_level   INTEGER  NOT NULL
target_level    INTEGER  NOT NULL
due_date        DATE
status          ENUM('pending', 'in_progress', 'achieved', 'overdue')  DEFAULT 'pending'
notes           TEXT
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### 1.4 Схема взаимодействия (REST API)

```
Фронтенд (React)  <-->  Бэкенд (FastAPI)  <-->  PostgreSQL
       |                      |
   JWT Token            Swagger / ReDoc
   (Authorization:     (документация)
    Bearer <token>)
```

Все запросы — REST JSON. Аутентификация через JWT (access + refresh token). Роль проверяется на бэкенде middleware/декоратором.

---

## 2. Архитектура и технологии

### 2.1 Обоснование выбора

| Компонент | Выбор | Почему |
|-----------|-------|--------|
| **Бэкенд** | FastAPI (Python) | Асинхронность из коробки, автогенерация OpenAPI/Swagger, Pydantic-валидация, отличная производительность. Знаком тестировщикам (Python — основной язык автотестов). |
| **Фронтенд** | React + Mantine (UI kit) | Mantine — лёгкий, 100+ компонентов, встроенная тёмная тема, Table, Modal, Forms — всё нужное есть. Vite как сборщик. |
| **БД** | PostgreSQL 15 | Надёжность, поддержка JSONB (для гибких метаданных), оконные функции для отчётов. |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic | Async-сессии под FastAPI, миграции через Alembic. |
| **Аутентификация** | JWT (access 30m + refresh 7d) + OAuth2 password flow | Простота реализации, stateless, поддержка в FastAPI из коробки. |
| **Деплой** | Docker + docker-compose | Консистентность окружений, простота развёртывания. |
| **CI/CD** | GitHub Actions | Бесплатно для приватных репо, огромная экосистема actions. |

### 2.2 Структура репозитория

```
/
├── backend/
│   ├── app/
│   │   ├── api/          # эндпоинты (v1/)
│   │   ├── core/         # config, security, dependencies
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── schemas/      # Pydantic схемы
│   │   ├── services/     # бизнес-логика
│   │   └── main.py       # entrypoint
│   ├── alembic/          # миграции
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # переиспользуемые компоненты
│   │   ├── pages/        # страницы
│   │   ├── api/          # клиент для API
│   │   ├── hooks/        # кастомные хуки
│   │   ├── store/        # состояние (zustand)
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .github/workflows/    # CI/CD
└── README.md
```

---

## 3. Настройка окружения и инфраструктуры

**Оценка: 1 день**

### Чек-лист

- [ ] Инициализация Git-репозитория, создание `main` + `develop` веток
- [ ] Настройка `.gitignore` (Python `__pycache__`, `node_modules`, `.env`, `*.pyc`)
- [ ] Создание `docker-compose.yml`:
  - `postgres:15` (volume для данных, порт 5432, healthcheck)
  - `backend` (build из `./backend`, порт 8000, зависит от postgres)
  - `frontend` (build из `./frontend`, порт 3000 / 80, зависит от backend)
- [ ] Бэкенд: `requirements.txt` (fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic, python-jose, passlib, httpx, pytest, pytest-asyncio)
- [ ] Бэкенд: настройка ruff + black (pyproject.toml)
- [ ] Фронтенд: инициализация React + Vite + TypeScript + Mantine
- [ ] Фронтенд: настройка ESLint + Prettier
- [ ] Настройка pre-commit хуков (ruff, eslint, trailing-whitespace)
- [ ] GitHub Actions:
  - Линтеры (ruff, eslint)
  - Тесты (pytest backend, vitest frontend)
  - Сборка Docker-образов и push в container registry
  - Деплой на staging (по пушу в `develop`)

---

## 4. Разработка бэкенда

**Оценка: 6 дней**

### День 1: каркас проекта, модели, миграции

- [ ] Создание `app/main.py`, `app/core/config.py` (BaseSettings из pydantic-settings)
- [ ] Подключение async SQLAlchemy + create_async_engine
- [ ] Модели: Employee, Team, Skill, Assessment, AssessmentHistory, IprPlan, IprGoal
- [ ] Alembic: `alembic init alembic`, настройка async Alembic, генерация миграции
- [ ] `app/core/database.py` — Dependency Injection сессии БД

### День 2: аутентификация и авторизация

- [ ] Хэширование паролей (passlib + bcrypt)
- [ ] Создание/верификация JWT (access + refresh) через `python-jose`
- [ ] Эндпоинты: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/register` (только для admin)
- [ ] Dependency `get_current_user` + проверка роли
- [ ] Middleware для проверки JWT

### День 3: CRUD сотрудников и навыков

- [ ] `GET /api/v1/employees` (админ/руководитель — все; сотрудник — только себя)
- [ ] `GET /api/v1/employees/{id}` (с проверкой прав)
- [ ] `POST /api/v1/employees` (admin)
- [ ] `PATCH /api/v1/employees/{id}` (admin)
- [ ] `GET /api/v1/skills` (все авторизованные)
- [ ] `POST /api/v1/skills`, `PATCH /api/v1/skills/{id}`, `DELETE /api/v1/skills/{id}` (admin)
- [ ] Фильтрация навыков по категории

### День 4: оценки (assessments)

- [ ] `GET /api/v1/assessments?employee_id=<id>` — получить все оценки сотрудника
- [ ] `GET /api/v1/assessments/matrix` — таблица employee × skill со свёрнутыми данными (доступно руководителю/admin)
- [ ] `PUT /api/v1/assessments/{skill_id}` — обновление самооценки (только свою) или оценки руководителя (manager_level)
- [ ] `PATCH /api/v1/assessments/{id}/target` — установка целевого уровня
- [ ] Валидация прав: сотрудник пишет только `self_level`, руководитель пишет `manager_level`

### День 5: история изменений и ИПР

- [ ] Триггер/сервис записи в `assessment_history` при изменении `*_level` в assessments
- [ ] `GET /api/v1/assessments/{id}/history` — история по конкретной оценке
- [ ] `GET /api/v1/ipr-plans?employee_id=<id>` — список ИПР
- [ ] `POST /api/v1/ipr-plans` — создание ИПР (руководитель, admin)
- [ ] `GET /api/v1/ipr-plans/{id}` с вложенными целями
- [ ] `PATCH /api/v1/ipr-plans/{id}` — обновление статуса, целей
- [ ] `POST /api/v1/ipr-plans/{id}/goals` — добавление цели в ИПР

### День 6: отчёты и экспорт

- [ ] `GET /api/v1/reports/team-summary` — распределение по грейдам, кол-во сотрудников, % покрытия навыками
- [ ] `GET /api/v1/reports/growth-zones` — навыки с наибольшим разрывом self vs manager
- [ ] `GET /api/v1/reports/comparison?employee_ids=...` — сравнение нескольких сотрудников
- [ ] `GET /api/v1/export/csv?type=matrix` — экспорт матрицы в CSV
- [ ] `GET /api/v1/export/excel?type=matrix` — экспорт в Excel (openpyxl)
- [ ] Seed-скрипт: наполнение БД тестовыми данными (5-10 сотрудников, 25+ навыков, оценки)

---

## 5. Разработка фронтенда

**Оценка: 6 дней**

### День 1: каркас проекта, маршрутизация, авторизация

- [ ] Инициализация Vite + React + TypeScript + Mantine
- [ ] Настройка роутинга (react-router-dom v6): `/login`, `/`, `/employees/:id`, `/matrix`, `/ipr`, `/admin`
- [ ] `api/client.ts` — axios-клиент с перехватчиком JWT (refresh token при 401)
- [ ] `store/auth.ts` — zustand store для состояния пользователя
- [ ] Страница логина (форма email + password), сохранение токена в localStorage
- [ ] ProtectedRoute — компонент-обёртка, редирект на `/login` если нет токена
- [ ] Layout: Sidebar (навигация по ролям) + Header (имя пользователя, logout)

### День 2: дашборд

- [ ] Карточки: всего сотрудников, распределение по грейдам (Junior/Middle/Senior)
- [ ] Bar chart: навыки × средний уровень (recharts / chart.js)
- [ ] Таблица "последние изменения" (last 10 history entries)
- [ ] Виджет "зоны роста": навыки с наибольшим разрывом self vs manager

### День 3: матрица компетенций

- [ ] Таблица: строки = сотрудники, колонки = навыки (сгруппированы по категориям)
- [ ] Цветовая индикация ячеек:
  - 1 — #ff6b6b (красный)
  - 2 — #ffa94d (оранжевый)
  - 3 — #ffd43b (жёлтый)
  - 4 — #69db7c (зелёный)
  - 5 — #2f9e44 (тёмно-зелёный)
- [ ] Если оценки нет — серый цвет / прочерк
- [ ] Отображение self/manager в одной ячейке (например "3 / 4")
- [ ] Клик по ячейке — модалка с деталями + кнопка редактирования (для руководителя)

### День 4: профиль сотрудника

- [ ] Информационная карточка (ФИО, роль, грейд, команда)
- [ ] Таблица навыков сотрудника с колонками: Навык | Самооценка | Оценка руководителя | Цель
- [ ] Режим редактирования самооценки (inline edit или модалка)
- [ ] Вкладка "История изменений" по каждому навыку
- [ ] Если текущий пользователь — руководитель: кнопка "Редактировать оценку" в каждой строке

### День 5: ИПР

- [ ] Список ИПР сотрудника (карточки: заголовок, статус, прогресс)
- [ ] Детальная страница ИПР:
  - Прогресс-бар по целям (сколько достигнуто из запланированного)
  - Таблица целей: навык | текущий | целевой | дедлайн | статус
  - Кнопка "Добавить цель" (для руководителя)
- [ ] Форма создания нового ИПР (выбор навыков, целевых уровней, дедлайнов)
- [ ] Drag-n-drop изменение статуса целей (kanban-style или select)

### День 6: администрирование и экспорт

- [ ] Страница управления навыками (таблица + форма добавления/редактирования, группировка по категориям)
- [ ] Страница управления пользователями (таблица + create/edit/disable)
- [ ] Кнопка экспорта матрицы в Excel (скачивание файла)
- [ ] Кнопка экспорта в CSV
- [ ] Финальная полировка UI: лоадеры, тосты (уведомления), подтверждение действий, пустые состояния, error boundary

---

## 6. Интеграция и тестирование

**Оценка: 3 дня**

### День 1: интеграционные тесты API

- [ ] Настройка pytest + pytest-asyncio + httpx AsyncClient
- [ ] Тестовая БД (отдельная PostgreSQL в docker-compose.test.yml или SQLite in-memory)
- [ ] Fixtures: test db session, test client, test user (admin, manager, employee)
- [ ] Тесты:
  - [ ] Аутентификация: успешный логин, неверный пароль, истекший токен
  - [ ] CRUD сотрудников: создание, получение, обновление, удаление (админ)
  - [ ] Проверка прав: сотрудник не может получить чужой профиль
  - [ ] Оценки: сотрудник ставит self_level, руководитель — manager_level
  - [ ] ИПР: создание плана, добавление целей
  - [ ] Отчёты: проверка агрегированных данных
  - [ ] Экспорт: файл скачивается, статус 200

### День 2: E2E-тесты (Playwright)

- [ ] Установка Playwright + настройка тестового окружения
- [ ] Сценарии:
  - [ ] Логин админа → переход на матрицу → просмотр
  - [ ] Логин руководителя → редактирование оценки подчинённого
  - [ ] Логин сотрудника → самооценка → проверка, что чужая матрица недоступна
  - [ ] Создание ИПР → добавление цели → изменение статуса
  - [ ] Экспорт в Excel (проверка что файл скачан)

### День 3: ручное тестирование и баг-фикс

- [ ] Проверка граничных случаев: пустая матрица, сотрудник без оценок
- [ ] Проверка производительности: матрица 50 сотрудников × 30 навыков (1500 ячеек)
- [ ] Проверка мобильной вёрстки (адаптивность)
- [ ] Сбор багов, фиксы

---

## 7. Документация и развёртывание

**Оценка: 2 дня**

### День 1: документация

- [ ] `README.md`:
  - Описание проекта
  - Быстрый старт: `docker-compose up`
  - Переменные окружения (POSTGRES_*, SECRET_KEY, JWT_*)
  - Команды для разработки (миграции, seed, тесты)
  - Архитектура (схема)
- [ ] API-документация: Swagger UI доступен по `/docs` (автоматически)
- [ ] `backend/app/api/v1/` — docstrings на русском/английском для каждого эндпоинта

### День 2: развёртывание

- [ ] Staging: сервер (VPS / выделенный), docker-compose, nginx reverse proxy
- [ ] Production: домен, SSL (Let's Encrypt через certbot), переменные окружения через `.env.prod`
- [ ] `docker-compose.prod.yml`: отдельные настройки (без монтирования кода, с volume для БД, ограничения ресурсов)
- [ ] Инструкция для пользователей (1-2 страницы, Google Docs или встроенная help-страница):
  - Как оценить свои навыки
  - Как руководителю выставить оценку
  - Как посмотреть матрицу команды
  - Как работать с ИПР

---

## 8. Риски и компромиссы

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Список навыков утверждён не сразу | Высокая | Среднее | Заложить 1 итерацию уточнения; MVP на подмножестве (15 навыков) |
| Нет выделенного дизайнера | Средняя | Низкое | Mantine-компоненты + готовые шаблоны; не тратить время на кастомный дизайн |
| Затягивание с настройкой CI/CD | Средняя | Среднее | Использовать шаблоны GitHub Actions из marketplace |
| Производительность матрицы при 50+ сотрудниках | Низкая | Среднее | Пагинация / виртуализация таблицы (TanStack Table) |
| Изменение прав доступа в процессе | Средняя | Низкое | Ролевая модель через enum; добавление роли — миграция + 1 строка кода |
| Отсутствие LDAP/SAML | Низкая | Среднее | Начать с формы логина; LDAP — задача на второй релиз |

### Компромиссы при дефиците времени

1. **MVP без отчётов** — дашборд ограничивается простой таблицей; отчёты и графики в версии 1.1.
2. **Упрощённый ИПР** — без drag-n-drop, без kanban; список целей с select статуса.
3. **Нет E2E-тестов** — только интеграционные тесты бэкенда + ручная проверка ключевых сценариев.
4. **Excel-экспорт через CSV** — вместо openpyxl, если нет времени на форматирование.

---

## 9. MVP: первые 2 недели

> Цель: получить работающее приложение, в котором можно:
> - Залогиниться
> - Посмотреть/отредактировать свои оценки
> - Руководителю — увидеть матрицу команды и выставить оценки
> - Экспорт в CSV

### Неделя 1

| День | Бэкенд | Фронтенд |
|------|--------|----------|
| 1 | Настройка проекта, модели, миграции | — |
| 2 | Аутентификация (логин, JWT) | Каркас React, роутинг, страница логина |
| 3 | CRUD сотрудников, CRUD навыков | Layout + дашборд (простой) |
| 4 | Оценки (self + manager), матрица | Страница профиля (самооценка) |
| 5 | История изменений (запись) | Матрица компетенций (таблица) |
| 6-7 | Интеграционные тесты + seed | Полировка, тосты, модалки |

### Неделя 2

| День | Бэкенд | Фронтенд |
|------|--------|----------|
| 1 | ИПР: CRUD, цели | Страница ИПР |
| 2 | Отчёты (team-summary, growth-zones) | Админка (навыки, пользователи) |
| 3 | Экспорт CSV/Excel | Экспорт (кнопки) |
| 4 | Доработки по тестам, баг-фикс | E2E-тесты (ключевые сценарии) |
| 5 | README, docker-compose финальный | Help-страница / инструкция |
| 6-7 | Финальное тестирование + деплой на staging | Финальное тестирование + деплой на staging |

---

## 10. Расширения после MVP

- Интеграция с корпоративным LDAP / SSO (OAuth2 + Azure AD / Keycloak)
- Импорт сотрудников из HR-системы (CSV/API)
- Уведомления (email/Telegram) — "руководитель выставил оценку", "дедлайн ИПР скоро"
- Вложения к ИПР (ссылки на курсы, материалы)
- Периодический ревью (напоминание каждые N месяцев)
- Сравнение по командам/отделам (если несколько команд)
- Лёгкая аналитика: тренды изменения навыков во времени
- Кастомные поля: linkedin, сертификаты, дата найма
- Темная тема (Mantine уже поддерживает)
