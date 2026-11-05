from typing import Any

from pydantic import BaseModel


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
