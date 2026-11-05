import asyncio
import os
from pathlib import Path

# Must happen before any app import: settings are read once, on first use.
TEST_DB_NAME = "subscription_tracker_test"
os.environ["DB_NAME"] = TEST_DB_NAME

import asyncpg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.settings import get_settings  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]
TABLES = "seat_assignments, subscriptions, employees, vendors, users, companies"


async def _create_test_database() -> None:
    db = get_settings().db
    conn = await asyncpg.connect(
        user=db.db_user,
        password=db.db_password,
        host=db.db_host,
        port=db.db_port,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """Build the schema through the real migrations, so they get tested too."""
    assert get_settings().db.db_name == TEST_DB_NAME
    asyncio.run(_create_test_database())
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")


@pytest.fixture(autouse=True)
async def clean_tables(test_database):
    yield
    # Guard: this wipes tables, so it must only ever run against the test database.
    assert engine.url.database == TEST_DB_NAME
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
def make_company(client):
    """Register a new company and return auth headers for its first user."""
    count = 0

    async def _make_company() -> dict[str, str]:
        nonlocal count
        count += 1
        credentials = {"email": f"owner{count}@acme.io", "password": "correct-horse-battery"}
        body = {"company_name": f"Company {count}", "full_name": "Owner", **credentials}
        assert (await client.post("/api/v1/auth/register", json=body)).status_code == 201
        login = await client.post("/api/v1/auth/login", json=credentials)
        return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

    return _make_company
