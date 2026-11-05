from typing import Annotated

from fastapi import APIRouter, Query

from app.database import DbSession
from app.project_schemas import APIResponse, Limit, Offset, Page
from modules.V1.AuthManager.dependencies import CurrentUser

from . import api_docs, controller
from .schemas import MonthlySpendRead, RenewalRead

router = APIRouter()


@router.get("/upcoming-renewals", **api_docs.RENEWALS)
async def upcoming_renewals(
    db: DbSession,
    user: CurrentUser,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    limit: Limit = 20,
    offset: Offset = 0,
) -> APIResponse[Page[RenewalRead]]:
    return await controller.upcoming_renewals_controller(db, user.company_id, days, limit, offset)


@router.get("/monthly-spend", **api_docs.SPEND)
async def monthly_spend(db: DbSession, user: CurrentUser) -> APIResponse[MonthlySpendRead]:
    return await controller.monthly_spend_controller(db, user.company_id)
