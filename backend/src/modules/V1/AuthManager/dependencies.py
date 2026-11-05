from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import DbSession
from app.security import decode_access_token

from .dao import AuthDAO
from .models import User

# auto_error=False lets us answer 401 in our own format when the header is missing.
bearer_scheme = HTTPBearer(auto_error=False, description="Token from POST /api/v1/auth/login")


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload["sub"])
    except ValueError as exc:
        raise unauthorized from exc
    # Loaded from the database so a deleted user's token stops working immediately.
    user = await AuthDAO.get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized
    return user


# Modules read user.company_id from here, never from client input.
CurrentUser = Annotated[User, Depends(get_current_user)]
