import asyncio

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.settings import get_settings

from .dao import AuthDAO
from .models import User
from .schemas import LoginRequest, RegisterRequest, TokenResponse

settings = get_settings()


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, payload: RegisterRequest) -> User:
        email_taken = HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        # bcrypt is deliberately slow, so it runs off the event loop to keep serving requests.
        password_hash = await asyncio.to_thread(hash_password, payload.password)
        try:
            # One transaction: the company and its first user are created together or not at all.
            async with db.begin():
                if await AuthDAO.get_user_by_email(db, payload.email):
                    raise email_taken
                return await AuthDAO.create_company_with_user(
                    db, payload.company_name, payload.email, password_hash, payload.full_name
                )
        except IntegrityError as exc:
            # Two simultaneous registrations can both pass the check; the unique constraint decides.
            raise email_taken from exc

    @staticmethod
    async def login(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
        user = await AuthDAO.get_user_by_email(db, payload.email)
        stored_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
        password_ok = await asyncio.to_thread(verify_password, payload.password, stored_hash)
        if not user or not password_ok:
            # Same response for both cases, so this can't be used to discover registered emails.
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
        return TokenResponse(
            access_token=create_access_token(user.id, user.company_id),
            expires_in_minutes=settings.security.access_token_expire_minutes,
        )
