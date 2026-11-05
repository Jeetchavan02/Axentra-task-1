import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.project_schemas import APIResponse

logger = logging.getLogger("uvicorn.error")


def _error_response(
    message: str, code: int, data: object = None, headers: dict[str, str] | None = None
) -> JSONResponse:
    body = APIResponse.error(message=message, code=code, data=data)
    return JSONResponse(status_code=code, content=body.model_dump(), headers=headers)


async def _handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(str(exc.detail), exc.status_code, headers=exc.headers)


async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Rejected input is left out on purpose: it could echo back a submitted password.
    errors = [
        {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return _error_response("Validation error", 422, {"errors": errors})


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # The traceback stays in the server log and never reaches the client.
    logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return _error_response("Internal server error", 500)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
