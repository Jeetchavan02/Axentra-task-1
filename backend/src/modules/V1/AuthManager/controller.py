from sqlalchemy.ext.asyncio import AsyncSession

from app.project_schemas import APIResponse

from .schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead
from .services import AuthService


async def register_controller(db: AsyncSession, payload: RegisterRequest) -> APIResponse[UserRead]:
    user = await AuthService.register(db, payload)
    return APIResponse[UserRead].success(
        data=UserRead.model_validate(user), message="Registered successfully", code=201
    )


async def login_controller(db: AsyncSession, payload: LoginRequest) -> APIResponse[TokenResponse]:
    token = await AuthService.login(db, payload)
    return APIResponse[TokenResponse].success(data=token, message="Logged in successfully")
