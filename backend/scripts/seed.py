"""Seed the database with test data: teams, skills, employees, and assessments."""

import asyncio

from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models import (
    Employee,
    EmployeeProfile,
    Team,
    Skill,
    Assessment,
    ReviewCycle,
    ReviewAssessment,
)


SKILLS_DATA = [
    (
        "ОС и инфраструктура",
        [
            "Linux (администрирование)",
            "Сети и протоколы",
            "Docker / контейнеризация",
            "Kubernetes (базовый)",
            "CI/CD (GitLab CI / Jenkins / GitHub Actions)",
        ],
    ),
    (
        "Базы данных",
        [
            "SQL (сложные запросы)",
            "PostgreSQL",
            "NoSQL (Redis, MongoDB)",
        ],
    ),
    (
        "Тестирование API",
        [
            "REST API (Postman / curl)",
            "GraphQL",
            "gRPC",
            "Нагрузочное тестирование (k6 / Locust / JMeter)",
        ],
    ),
    (
        "Тестирование UI",
        [
            "Selenium / Playwright / Cypress",
            "HTML/CSS (basics)",
            "Кроссбраузерное тестирование",
            "Accessibility",
        ],
    ),
    (
        "Автоматизация",
        [
            "pytest / PyTest + Selenium",
            "Page Object Model",
            "Allure-отчёты",
            "Написание кастомных утилит",
        ],
    ),
    (
        "TMS и процессы",
        [
            "TestRail / Zephyr / Allure TestOps",
            "Jira / YouTrack",
            "Тест-дизайн (эквивалентность, граничные значения)",
        ],
    ),
    (
        "Программирование",
        [
            "Python (автотесты, скрипты)",
            "TypeScript / JavaScript (базовый)",
            "Bash-скриптинг",
        ],
    ),
    (
        "Софт-скиллы",
        [
            "Наставничество",
            "Планирование и оценка задач",
            "Код-ревью автотестов",
        ],
    ),
]


async def seed():
    async with async_session_factory() as session:
        # Clean existing data
        for table in [
            ReviewAssessment,
            ReviewCycle,
            Assessment,
            EmployeeProfile,
            Employee,
            Skill,
            Team,
        ]:
            await session.execute(table.__table__.delete())

        team_qa = Team(name="QA Engineering", description="Команда тестирования")
        team_auto = Team(name="Automation QA", description="Команда автоматизации")
        session.add_all([team_qa, team_auto])
        await session.flush()

        employees = [
            Employee(
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                full_name="Админ Админов",
                role="admin",
                grade="senior",
                team_id=team_qa.id,
            ),
            Employee(
                email="manager@example.com",
                password_hash=hash_password("manager123"),
                full_name="Менеджер Менеджеров",
                role="manager",
                grade="senior",
                team_id=team_qa.id,
            ),
            Employee(
                email="expert@example.com",
                password_hash=hash_password("expert123"),
                full_name="Эксперт Экспертов",
                role="expert",
                grade="senior",
                team_id=team_qa.id,
            ),
            Employee(
                email="ivan@example.com",
                password_hash=hash_password("ivan123"),
                full_name="Иванов Иван",
                role="employee",
                grade="middle",
                team_id=team_qa.id,
            ),
            Employee(
                email="petr@example.com",
                password_hash=hash_password("petr123"),
                full_name="Петров Пётр",
                role="employee",
                grade="junior",
                team_id=team_auto.id,
            ),
            Employee(
                email="anna@example.com",
                password_hash=hash_password("anna123"),
                full_name="Анна Смирнова",
                role="employee",
                grade="middle",
                team_id=team_auto.id,
            ),
            Employee(
                email="olga@example.com",
                password_hash=hash_password("olga123"),
                full_name="Ольга Кузнецова",
                role="employee",
                grade="junior",
                team_id=team_qa.id,
            ),
            Employee(
                email="dmitry@example.com",
                password_hash=hash_password("dmitry123"),
                full_name="Дмитрий Новиков",
                role="employee",
                grade="senior",
                team_id=team_auto.id,
            ),
        ]
        session.add_all(employees)
        await session.flush()

        WEIGHTS: dict[str, int] = {
            "pytest": 3,
            "Selenium": 3,
            "Playwright": 3,
            "Cypress": 3,
            "Page Object Model": 3,
            "Allure": 2,
            "REST API": 3,
            "Postman": 3,
            "GraphQL": 2,
            "gRPC": 2,
            "Нагрузочное тестирование": 3,
            "k6": 3,
            "Locust": 3,
            "JMeter": 3,
            "Linux": 2,
            "Docker": 2,
            "Kubernetes": 2,
            "CI/CD": 3,
            "GitLab CI": 3,
            "Jenkins": 3,
            "GitHub Actions": 3,
            "SQL": 3,
            "PostgreSQL": 2,
            "NoSQL": 2,
            "HTML/CSS": 1,
            "Accessibility": 1,
            "Кроссбраузерное": 1,
            "TestRail": 2,
            "Zephyr": 2,
            "Allure TestOps": 2,
            "Jira": 1,
            "YouTrack": 1,
            "Тест-дизайн": 3,
            "Python": 3,
            "TypeScript": 2,
            "Bash": 1,
            "Наставничество": 2,
            "Планирование": 3,
            "Код-ревью": 2,
        }

        skills = []
        order = 0
        for category, names in SKILLS_DATA:
            for name in names:
                w = 1
                for key, val in WEIGHTS.items():
                    if key.lower() in name.lower():
                        w = val
                        break
                skills.append(
                    Skill(
                        name=name,
                        category=category,
                        weight=w,
                        sort_order=order,
                        description=f"Навык: {name}",
                    )
                )
                order += 10
        session.add_all(skills)
        await session.flush()

        assessments = []
        import random

        for emp in employees:
            if emp.role == "admin":
                continue
            for skill in skills:
                self_lvl = random.randint(2, 4)
                mgr_lvl = random.randint(1, 4)
                assessments.append(
                    Assessment(
                        employee_id=emp.id,
                        skill_id=skill.id,
                        self_level=self_lvl,
                        manager_level=mgr_lvl,
                        target_level=min(self_lvl + random.randint(0, 1), 4),
                        updated_by=emp.id,
                    )
                )
        session.add_all(assessments)

        profiles = []
        for emp in employees:
            profiles.append(
                EmployeeProfile(
                    employee_id=emp.id,
                    organization="ВРМ",
                    city="Санкт-Петербург",
                    department="Департамент тестирования",
                    subdivision="Отдел тестирования ВРМ",
                    position="Инженер по тестированию",
                    specialization="Автоматизация тестирования",
                    experience=random.randint(8, 12),
                    education=random.randint(8, 12),
                    task_complexity=random.randint(8, 12),
                    autonomy=random.randint(8, 12),
                    communication=random.randint(8, 12),
                    control=random.randint(8, 12),
                    mentoring=random.randint(8, 12),
                    responsibility=random.randint(8, 12),
                    technical_competencies=random.randint(8, 12),
                )
            )
        session.add_all(profiles)
        await session.commit()

    print(
        f"Seeded: {len(employees)} employees, {len(skills)} skills, {len(assessments)} assessments, {len(profiles)} profiles"
    )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
