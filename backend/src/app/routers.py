from fastapi import FastAPI

from modules.V1.V1routers import router as v1_router


def register_routers(app: FastAPI) -> None:
    app.include_router(v1_router, prefix="/api/v1")
