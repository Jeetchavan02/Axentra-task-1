import asyncio
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import func, select, text

from app.database import SessionFactory
from app.settings import get_settings
from modules.V1.AuthManager.dao import AuthDAO
from modules.V1.models import Company, User

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
PASSWORD = "correct-horse-battery"
security = get_settings().security


def register_body(**overrides) -> dict:
    return {
        "company_name": "Acme",
        "full_name": "Asha Rao",
        "email": "asha@acme.io",
        "password": PASSWORD,
    } | overrides


async def login_token(client, email="asha@acme.io", password=PASSWORD) -> str:
    response = await client.post(LOGIN, json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_token(secret=None, algorithm=None, **claims) -> str:
    payload = {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=5)} | claims
    return jwt.encode(
        payload, secret or security.jwt_secret, algorithm=algorithm or security.jwt_algorithm
    )


async def count(model) -> int:
    async with SessionFactory() as db:
        return await db.scalar(select(func.count()).select_from(model))


# ---------------------------------------- Register ----------------------------------------


async def test_register_creates_company_and_user(client):
    response = await client.post(REGISTER, json=register_body())

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 201
    assert body["data"]["email"] == "asha@acme.io"
    assert await count(Company) == 1
    assert await count(User) == 1


async def test_register_never_returns_or_stores_plain_password(client):
    response = await client.post(REGISTER, json=register_body())

    assert PASSWORD not in response.text
    assert "password" not in response.json()["data"]
    async with SessionFactory() as db:
        stored = await db.scalar(select(User.password_hash))
    assert stored != PASSWORD
    assert stored.startswith("$2")


async def test_duplicate_email_is_rejected_ignoring_case(client):
    await client.post(REGISTER, json=register_body())

    response = await client.post(REGISTER, json=register_body(email="ASHA@acme.io"))

    assert response.status_code == 409
    assert await count(Company) == 1, "A rejected registration must not leave a company behind"


async def test_simultaneous_registrations_create_one_account(client):
    responses = await asyncio.gather(
        *(client.post(REGISTER, json=register_body()) for _ in range(5))
    )

    assert sorted(r.status_code for r in responses) == [201, 409, 409, 409, 409]
    assert await count(User) == 1
    assert await count(Company) == 1, "Losing requests must roll back their company"


async def test_unique_constraint_race_returns_409_and_rolls_back(client, monkeypatch):
    """Forces the race: the pre-check sees no user, so only the constraint can stop the insert."""
    await client.post(REGISTER, json=register_body())

    async def email_looks_free(*_):
        return None

    monkeypatch.setattr(AuthDAO, "get_user_by_email", email_looks_free)
    response = await client.post(REGISTER, json=register_body())

    assert response.status_code == 409
    assert await count(User) == 1
    assert await count(Company) == 1, "The losing request must roll back its company"


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"password": "short"},
        {"password": "x" * 73},
        {"company_name": "   "},
        {"full_name": ""},
    ],
)
async def test_invalid_registration_is_rejected(client, overrides):
    response = await client.post(REGISTER, json=register_body(**overrides))

    assert response.status_code == 422
    assert response.json()["status"] == "error"
    assert await count(User) == 0


async def test_validation_error_does_not_echo_password(client):
    response = await client.post(REGISTER, json=register_body(password="sh0rt"))

    assert response.status_code == 422
    assert "sh0rt" not in response.text


async def test_client_cannot_choose_company_id(client):
    response = await client.post(REGISTER, json=register_body(company_id=999))

    assert response.status_code == 201
    assert response.json()["data"]["company_id"] != 999


# ----------------------------------------- Login -----------------------------------------


async def test_login_returns_token_with_user_and_company(client):
    created = (await client.post(REGISTER, json=register_body())).json()["data"]

    claims = jwt.decode(
        await login_token(client), security.jwt_secret, algorithms=[security.jwt_algorithm]
    )

    assert claims["sub"] == str(created["id"])
    assert claims["company_id"] == created["company_id"]


async def test_login_email_ignores_case(client):
    await client.post(REGISTER, json=register_body())

    assert await login_token(client, email="ASHA@ACME.IO")


async def test_wrong_password_and_unknown_email_look_identical(client):
    await client.post(REGISTER, json=register_body())

    wrong = await client.post(LOGIN, json={"email": "asha@acme.io", "password": "wrong-password"})
    unknown = await client.post(LOGIN, json={"email": "nobody@acme.io", "password": PASSWORD})

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_overlong_login_password_fails_cleanly(client):
    await client.post(REGISTER, json=register_body())

    response = await client.post(LOGIN, json={"email": "asha@acme.io", "password": "x" * 100})

    assert response.status_code == 401


# -------------------------------------- Protected routes --------------------------------------


async def test_me_returns_logged_in_user(client):
    await client.post(REGISTER, json=register_body())

    response = await client.get(ME, headers=bearer(await login_token(client)))

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "asha@acme.io"


async def test_me_without_token_uses_standard_401(client):
    response = await client.get(ME)

    assert response.status_code == 401
    assert response.json()["status"] == "error"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token",
    [
        "garbage",
        make_token(exp=datetime.now(UTC) - timedelta(minutes=1)),
        make_token(secret="an-attacker-secret-that-is-long-enough-to-use"),
        make_token(algorithm="HS512"),
        make_token(sub="not-a-number"),
        jwt.encode({"sub": "1"}, security.jwt_secret, algorithm=security.jwt_algorithm),
        jwt.encode({"sub": "1", "exp": 9999999999}, key="", algorithm="none"),
    ],
    ids=["garbage", "expired", "wrong-secret", "wrong-algorithm", "bad-sub", "no-exp", "alg-none"],
)
async def test_bad_tokens_are_rejected(client, token):
    await client.post(REGISTER, json=register_body())

    response = await client.get(ME, headers=bearer(token))

    assert response.status_code == 401


async def test_token_stops_working_after_user_is_deleted(client):
    await client.post(REGISTER, json=register_body())
    token = await login_token(client)
    async with SessionFactory() as db:
        await db.execute(text("DELETE FROM users"))
        await db.commit()

    response = await client.get(ME, headers=bearer(token))

    assert response.status_code == 401
