from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.security import BCRYPT_MAX_BYTES

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


def _normalize_email(email: str) -> str:
    return email.lower()


class RegisterRequest(BaseModel):
    company_name: Name
    full_name: Name
    email: EmailStr
    password: str = Field(min_length=8)

    _lower_email = field_validator("email")(_normalize_email)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, password: str) -> str:
        if len(password.encode()) > BCRYPT_MAX_BYTES:
            raise ValueError(f"Password must be at most {BCRYPT_MAX_BYTES} bytes")
        return password


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=1024)

    _lower_email = field_validator("email")(_normalize_email)


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
