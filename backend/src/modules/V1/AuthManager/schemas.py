from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.project_schemas import Name, NormalizedEmail
from app.security import BCRYPT_MAX_BYTES


class RegisterRequest(BaseModel):
    company_name: Name
    full_name: Name
    email: NormalizedEmail
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, password: str) -> str:
        if len(password.encode()) > BCRYPT_MAX_BYTES:
            raise ValueError(f"Password must be at most {BCRYPT_MAX_BYTES} bytes")
        return password


class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(max_length=1024)


class UserRead(BaseModel):
    """Deliberately has no password field, so a hash can't reach a response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    email: EmailStr
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
