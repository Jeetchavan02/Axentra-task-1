from typing import Annotated, Any

from fastapi import Path, Query
from pydantic import AfterValidator, BaseModel, EmailStr, StringConstraints

POSTGRES_INT_MAX = 2_147_483_647
NO_NUL_BYTES = r"^[^\x00]*$"  # Postgres text can't store NUL, so reject it as bad input.

Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255, pattern=NO_NUL_BYTES),
]
NormalizedEmail = Annotated[EmailStr, AfterValidator(str.lower)]

# Limits keep out-of-range values a 422 instead of a database error and a 500.
ResourceId = Annotated[int, Path(gt=0, le=POSTGRES_INT_MAX)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=POSTGRES_INT_MAX)]
Search = Annotated[str | None, Query(max_length=255, pattern=NO_NUL_BYTES)]


class APIResponse[T](BaseModel):
    """Envelope returned by every endpoint. `code` always matches the HTTP status."""

    code: int
    message: str
    status: str
    data: T | None = None

    @classmethod
    def success(cls, data: T | None = None, message: str = "Success", code: int = 200):
        return cls(code=code, message=message, status="success", data=data)

    @classmethod
    def error(cls, message: str, code: int, data: Any = None) -> "APIResponse[Any]":
        return APIResponse[Any](code=code, message=message, status="error", data=data)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
