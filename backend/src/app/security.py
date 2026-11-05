from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.settings import get_settings

settings = get_settings()

BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    encoded = password.encode()
    if len(encoded) > BCRYPT_MAX_BYTES:
        return False
    return bcrypt.checkpw(encoded, password_hash.encode())


# Checked when an email is unknown, so that login takes the same time either way
# and response timing can't reveal which emails are registered.
DUMMY_PASSWORD_HASH = hash_password("timing-equalizer")


def create_access_token(user_id: int, company_id: int) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.security.access_token_expire_minutes)
    payload = {"sub": str(user_id), "company_id": company_id, "iat": now, "exp": expires_at}
    return jwt.encode(
        payload, settings.security.jwt_secret, algorithm=settings.security.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Pinning the algorithm blocks forged tokens that claim a different one, such as "none".
        return jwt.decode(
            token,
            settings.security.jwt_secret,
            algorithms=[settings.security.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError as exc:
        raise invalid from exc
