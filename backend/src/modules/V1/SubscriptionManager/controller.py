from sqlalchemy.ext.asyncio import AsyncSession

from app.project_schemas import APIResponse, Page

from .dao import SubscriptionDAO
from .models import SubscriptionStatus
from .schemas import SubscriptionRead, SubscriptionWrite
from .services import SubscriptionService


async def create_subscription_controller(
    db: AsyncSession, company_id: int, payload: SubscriptionWrite
) -> APIResponse[SubscriptionRead]:
    subscription = await SubscriptionService.create(db, company_id, payload)
    return APIResponse[SubscriptionRead].success(
        data=SubscriptionRead.model_validate(subscription),
        message="Subscription created",
        code=201,
    )


async def list_subscriptions_controller(
    db: AsyncSession,
    company_id: int,
    limit: int,
    offset: int,
    search: str | None,
    status: SubscriptionStatus | None,
    vendor_id: int | None,
) -> APIResponse[Page[SubscriptionRead]]:
    rows, total = await SubscriptionDAO.list(
        db, company_id, limit, offset, search, status, vendor_id
    )
    page = Page[SubscriptionRead](
        items=[SubscriptionRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
    return APIResponse[Page[SubscriptionRead]].success(data=page)


async def get_subscription_controller(
    db: AsyncSession, company_id: int, subscription_id: int
) -> APIResponse[SubscriptionRead]:
    subscription = await SubscriptionService.get(db, company_id, subscription_id)
    return APIResponse[SubscriptionRead].success(data=SubscriptionRead.model_validate(subscription))


async def update_subscription_controller(
    db: AsyncSession, company_id: int, subscription_id: int, payload: SubscriptionWrite
) -> APIResponse[SubscriptionRead]:
    subscription = await SubscriptionService.update(db, company_id, subscription_id, payload)
    return APIResponse[SubscriptionRead].success(
        data=SubscriptionRead.model_validate(subscription), message="Subscription updated"
    )


async def delete_subscription_controller(
    db: AsyncSession, company_id: int, subscription_id: int
) -> APIResponse[dict[str, int]]:
    await SubscriptionService.delete(db, company_id, subscription_id)
    return APIResponse[dict[str, int]].success(
        data={"id": subscription_id}, message="Subscription deleted"
    )
