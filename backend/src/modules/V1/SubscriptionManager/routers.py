from typing import Annotated

from fastapi import APIRouter, Query, status

from app.database import DbSession
from app.project_schemas import (
    POSTGRES_INT_MAX,
    APIResponse,
    Limit,
    Offset,
    Page,
    ResourceId,
    Search,
)
from modules.V1.AuthManager.dependencies import CurrentUser

from . import api_docs, controller
from .models import SubscriptionStatus
from .schemas import SubscriptionRead, SubscriptionWrite

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, **api_docs.CREATE)
async def create_subscription(
    db: DbSession, user: CurrentUser, payload: SubscriptionWrite
) -> APIResponse[SubscriptionRead]:
    return await controller.create_subscription_controller(db, user.company_id, payload)


@router.get("", **api_docs.LIST)
async def list_subscriptions(
    db: DbSession,
    user: CurrentUser,
    limit: Limit = 20,
    offset: Offset = 0,
    search: Search = None,
    status: SubscriptionStatus | None = None,
    vendor_id: Annotated[int | None, Query(gt=0, le=POSTGRES_INT_MAX)] = None,
) -> APIResponse[Page[SubscriptionRead]]:
    return await controller.list_subscriptions_controller(
        db, user.company_id, limit, offset, search, status, vendor_id
    )


@router.get("/{subscription_id}", **api_docs.GET)
async def get_subscription(
    db: DbSession, user: CurrentUser, subscription_id: ResourceId
) -> APIResponse[SubscriptionRead]:
    return await controller.get_subscription_controller(db, user.company_id, subscription_id)


@router.put("/{subscription_id}", **api_docs.UPDATE)
async def update_subscription(
    db: DbSession, user: CurrentUser, subscription_id: ResourceId, payload: SubscriptionWrite
) -> APIResponse[SubscriptionRead]:
    return await controller.update_subscription_controller(
        db, user.company_id, subscription_id, payload
    )


@router.delete("/{subscription_id}", **api_docs.DELETE)
async def delete_subscription(
    db: DbSession, user: CurrentUser, subscription_id: ResourceId
) -> APIResponse[dict[str, int]]:
    return await controller.delete_subscription_controller(db, user.company_id, subscription_id)
