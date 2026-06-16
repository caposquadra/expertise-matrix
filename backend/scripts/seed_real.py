"""Seed the database with real employee data matching provided list."""

import asyncio
import random

from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models import (
    Employee,
    EmployeeProfile,
    SkillGradeTarget,
    Team,
    Skill,
    Assessment,
    ReviewCycle,
    ReviewAssessment,
)


SKILLS_DATA: list[tuple[str, list[tuple[str, int, int, int]]]] = [
    (
        "Основы тестирования и тестовая документация",
        [
            ("Базовые знания о тестировании и контроле качества", 1, 2, 3),
            ("Знание типов и видов тестирования", 1, 2, 3),
            ("Анализ и тестирование требований и дизайнов", 1, 2, 3),
            ("Знание тестовой стратегии и тестового плана", 1, 2, 3),
            ("Знание методологий разработки ПО (SCRUM, Kanban, Waterfall)", 1, 2, 2),
            (
                "Подготовка тестовой документации (чекисты, сценарии, ПМИ, отчёты об ошибках, протоколы)",
                1,
                2,
                3,
            ),
            ("Работа в Tooster", 2, 2, 2),
        ],
    ),
    (
        "Функциональное тестирование",
        [
            ("Тестирование API", 1, 2, 3),
            ("Тестирование WEB", 1, 2, 3),
            ("Проведение интеграционного тестирования", 1, 2, 3),
            ("Тестирование совместимости с разными дистрибутивами и версиями", 1, 2, 2),
            ("Нахождение дефектов, работа в Ева / Redmine", 1, 2, 3),
            ("Подготовка отчетов по итогам тестирования", 0, 1, 3),
        ],
    ),
    (
        "Инструменты / Технические навыки",
        [
            (
                "Знание интернет-технологий (HTML, CSS, DOM, протоколы, HTTP, DevTools)",
                1,
                2,
                3,
            ),
            ("Основы сетей", 1, 2, 3),
            ("Знания Linux", 2, 2, 3),
            ("Работа с базами данных, знание SQL", 1, 2, 2),
            ("Нагрузочное тестирование (Jmeter, Locust, К6)", 0, 1, 2),
            ("Тестирование безопасности", 1, 1, 2),
            ("Автоматизация API и UI (инструменты, фреймворки)", 1, 2, 2),
            ("Знание языка программирования (Python, JAVA, TypeScript)", 1, 2, 2),
            ("Инструменты CI/CD (Jenkins, GitLab CI/CD, GitHub Actions)", 1, 1, 2),
            ("Docker / Kubernetes", 1, 1, 2),
            ("Работа с очередями и брокерами сообщений (Kafka, RabbitMQ)", 0, 1, 2),
            ("Системы логирования / мониторинга (Grafana, ELK)", 0, 1, 2),
            ("Работа с ИИ", 1, 2, 2),
        ],
    ),
    (
        "Проектная работа: знание продукта",
        [
            ("Участие в тестировании РЕД ОС", 1, 2, 3),
            ("Участие в тестировании РЕД ВРМ", 1, 2, 3),
            ("Участие в тестировании РЕД Виртуализация", 1, 2, 3),
            ("Участие в тестировании РЕД АДМ", 1, 2, 3),
            ("Участие в тестировании РЕД К", 1, 2, 3),
        ],
    ),
]

GRADE_NAMES = ["junior", "middle", "senior"]

EMPLOYEES_DATA = [
    ("Зимин Дмитрий", "senior", "Старший инженер по тестированию"),
    ("Волков Никита", "senior", "Старший инженер по тестированию"),
    ("Саукова Екатерина", "middle", "Инженер по тестированию"),
    ("Базуев Роман", "middle", "Инженер по тестированию"),
    ("Годунов Вячеслав", "middle", "Инженер по тестированию"),
    ("Кузьмин Александр", "middle", "Инженер по тестированию"),
    ("Барыгин Иван", "middle", "Инженер по тестированию"),
    ("Евланов Максим", "middle", "Инженер по тестированию"),
    ("Уксусова Алена", "middle", "Инженер по тестированию"),
    ("Воронкович Артур", "junior", "Младший инженер-тестировщик"),
]


async def seed():
    async with async_session_factory() as session:
        for table in [
            ReviewAssessment,
            ReviewCycle,
            Assessment,
            SkillGradeTarget,
            EmployeeProfile,
            Employee,
            Skill,
            Team,
        ]:
            await session.execute(table.__table__.delete())

        team_qa = Team(name="QA Engineering", description="Команда тестирования ВРМ")
        session.add(team_qa)
        await session.flush()

        system_users = [
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
        ]
        session.add_all(system_users)
        await session.flush()

        employees = []
        for full_name, grade, position in EMPLOYEES_DATA:
            email = f"{full_name.split()[0].lower()}@example.com"
            emp = Employee(
                email=email,
                password_hash=hash_password("employee123"),
                full_name=full_name,
                role="employee",
                grade=grade,
                team_id=team_qa.id,
            )
            session.add(emp)
            employees.append((emp, position))
        await session.flush()

        skills = []
        order = 0
        for category, items in SKILLS_DATA:
            for name, jl, ml, sl in items:
                w = (
                    3
                    if category == "Инструменты / Технические навыки"
                    else 2
                    if category
                    in (
                        "Проектная работа: знание продукта",
                        "Функциональное тестирование",
                    )
                    else 1
                )
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

        skill_map: dict[str, Skill] = {s.name: s for s in skills}
        targets = []
        for category, items in SKILLS_DATA:
            for name, jl, ml, sl in items:
                skill = skill_map[name]
                for grade, level in [("junior", jl), ("middle", ml), ("senior", sl)]:
                    targets.append(
                        SkillGradeTarget(
                            skill_id=skill.id,
                            grade=grade,
                            expected_level=level,
                        )
                    )
        session.add_all(targets)

        targets_data: dict[str, list[int]] = {}
        for category, items in SKILLS_DATA:
            for name, jl, ml, sl in items:
                targets_data[name] = [jl, ml, sl]

        assessments = []
        for emp, _ in employees:
            grade_idx = GRADE_NAMES.index(emp.grade) if emp.grade in GRADE_NAMES else 1
            next_idx = min(grade_idx + 1, len(GRADE_NAMES) - 1)
            for skill in skills:
                expected = targets_data[skill.name][grade_idx]
                next_expected = targets_data[skill.name][next_idx]
                assessments.append(
                    Assessment(
                        employee_id=emp.id,
                        skill_id=skill.id,
                        self_level=expected,
                        manager_level=expected,
                        target_level=next_expected,
                        updated_by=emp.id,
                    )
                )
        session.add_all(assessments)

        profiles = []
        for emp, position in employees:
            profiles.append(
                EmployeeProfile(
                    employee_id=emp.id,
                    organization="РЕД СОФТ",
                    city="Санкт-Петербург",
                    department="Департамент тестирования",
                    subdivision="Отдел тестирования ВРМ",
                    position=position,
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
        f"Seeded: {len(system_users) + len(employees)} employees, "
        f"{len(skills)} skills, "
        f"{len(assessments)} assessments, "
        f"{len(profiles)} profiles, "
        f"{len(targets)} grade targets"
    )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
