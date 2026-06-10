import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import Employee, Skill

TEST_DB_URL = "postgresql+asyncpg://app:app_secret@postgres:5432/expertise_matrix_test"

seed_engine = create_async_engine(TEST_DB_URL, echo=False)
seed_session_factory = async_sessionmaker(
    seed_engine, class_=AsyncSession, expire_on_commit=False
)

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    try:
        async with seed_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        master_engine = create_async_engine(
            TEST_DB_URL.replace("expertise_matrix_test", "postgres"),
            isolation_level="AUTOCOMMIT",
        )
        async with master_engine.connect() as conn:
            await conn.execute(text("CREATE DATABASE expertise_matrix_test"))
        await master_engine.dispose()
    proc = await asyncio.create_subprocess_exec(
        "alembic",
        "upgrade",
        "head",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Alembic upgrade failed: {stderr.decode()}")
    yield
    async with seed_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        await conn.run_sync(Base.metadata.drop_all)
    await seed_engine.dispose()
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def admin_user(setup_database) -> Employee:
    async with seed_session_factory() as session:
        user = Employee(
            email="admin@test.com",
            password_hash=hash_password("admin123"),
            full_name="Test Admin",
            role="admin",
            grade="senior",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture(scope="session")
async def manager_user(setup_database) -> Employee:
    async with seed_session_factory() as session:
        user = Employee(
            email="manager@test.com",
            password_hash=hash_password("manager123"),
            full_name="Test Manager",
            role="manager",
            grade="middle",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture(scope="session")
async def employee_user(setup_database) -> Employee:
    async with seed_session_factory() as session:
        user = Employee(
            email="employee@test.com",
            password_hash=hash_password("employee123"),
            full_name="Test Employee",
            role="employee",
            grade="junior",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture(scope="session")
async def expert_user(setup_database) -> Employee:
    async with seed_session_factory() as session:
        user = Employee(
            email="expert@test.com",
            password_hash=hash_password("expert123"),
            full_name="Test Expert",
            role="expert",
            grade="senior",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture(scope="session")
async def skill(setup_database) -> Skill:
    async with seed_session_factory() as session:
        s = Skill(
            name="Linux",
            category="ОС и инфраструктура",
            description="Test",
            sort_order=1,
        )
        session.add(s)
        await session.commit()
        await session.refresh(s)
        return s


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as connection:
        async with connection.begin() as transaction:
            async_session = async_sessionmaker(
                bind=connection, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                yield session
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def get_token(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: Employee) -> str:
    return await get_token(client, "admin@test.com", "admin123")


@pytest_asyncio.fixture
async def manager_token(client: AsyncClient, manager_user: Employee) -> str:
    return await get_token(client, "manager@test.com", "manager123")


@pytest_asyncio.fixture
async def employee_token(client: AsyncClient, employee_user: Employee) -> str:
    return await get_token(client, "employee@test.com", "employee123")


@pytest_asyncio.fixture
async def expert_token(client: AsyncClient, expert_user: Employee) -> str:
    return await get_token(client, "expert@test.com", "expert123")
