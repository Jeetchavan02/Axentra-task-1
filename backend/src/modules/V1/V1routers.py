from fastapi import APIRouter

from app.project_schemas import APIResponse

router = APIRouter()

# Feature module routers are attached here as they are built.


@router.get("/ping", tags=["monitoring"])
async def ping() -> APIResponse[dict[str, str]]:
    return APIResponse[dict[str, str]].success(data={"api": "v1"})
