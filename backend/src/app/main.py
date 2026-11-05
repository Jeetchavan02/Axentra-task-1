from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.error_handlers import register_error_handlers
from app.project_schemas import APIResponse
from app.routers import register_routers
from app.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app.project_name, version=settings.app.api_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
register_routers(app)


@app.get("/health", tags=["monitoring"])
async def health_check() -> APIResponse[dict[str, str]]:
    return APIResponse[dict[str, str]].success(data={"status": "ok"})
