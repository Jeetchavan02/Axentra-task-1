from fastapi import APIRouter, status

from app.database import DbSession
from app.project_schemas import APIResponse

from . import api_docs
from .controller import login_controller, register_controller
from .schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, **api_docs.REGISTER)
async def register(db: DbSession, payload: RegisterRequest) -> APIResponse[UserRead]:
    return await register_controller(db, payload)


@router.post("/login", **api_docs.LOGIN)
async def login(db: DbSession, payload: LoginRequest) -> APIResponse[TokenResponse]:
    return await login_controller(db, payload)
