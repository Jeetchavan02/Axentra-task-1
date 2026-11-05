from fastapi import APIRouter, status

from app.database import DbSession
from app.project_schemas import APIResponse, Limit, Offset, Page, ResourceId
from modules.V1.AuthManager.dependencies import CurrentUser

from . import api_docs, controller
from .schemas import SeatCreate, SeatRead

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, **api_docs.ASSIGN)
async def assign_seat(
    db: DbSession, user: CurrentUser, subscription_id: ResourceId, payload: SeatCreate
) -> APIResponse[SeatRead]:
    return await controller.assign_seat_controller(db, user.company_id, subscription_id, payload)


@router.get("", **api_docs.LIST)
async def list_seats(
    db: DbSession,
    user: CurrentUser,
    subscription_id: ResourceId,
    limit: Limit = 20,
    offset: Offset = 0,
) -> APIResponse[Page[SeatRead]]:
    return await controller.list_seats_controller(
        db, user.company_id, subscription_id, limit, offset
    )


@router.delete("/{employee_id}", **api_docs.REMOVE)
async def remove_seat(
    db: DbSession, user: CurrentUser, subscription_id: ResourceId, employee_id: ResourceId
) -> APIResponse[dict[str, int]]:
    return await controller.remove_seat_controller(
        db, user.company_id, subscription_id, employee_id
    )
