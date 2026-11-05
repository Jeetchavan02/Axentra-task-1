from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.V1.SeatManager.models import SeatAssignment

from .models import Subscription, SubscriptionStatus


class SubscriptionDAO:
    """Every query filters by company_id, so one company can't reach another's subscriptions."""

    @staticmethod
    async def get(
        db: AsyncSession, company_id: int, subscription_id: int, *, lock: bool = False
    ) -> Subscription | None:
        query = select(Subscription).where(
            Subscription.id == subscription_id, Subscription.company_id == company_id
        )
        if lock:
            # Holds the row until commit, so seat changes on it have to wait their turn.
            query = query.with_for_update()
        return await db.scalar(query)

    @staticmethod
    async def list(
        db: AsyncSession,
        company_id: int,
        limit: int,
        offset: int,
        search: str | None,
        status: SubscriptionStatus | None,
        vendor_id: int | None,
    ) -> tuple[list[Subscription], int]:
        conditions = [Subscription.company_id == company_id]
        if search:
            conditions.append(Subscription.plan_name.icontains(search, autoescape=True))
        if status:
            conditions.append(Subscription.status == status)
        if vendor_id:
            conditions.append(Subscription.vendor_id == vendor_id)
        total = await db.scalar(select(func.count()).select_from(Subscription).where(*conditions))
        rows = await db.scalars(
            select(Subscription)
            .where(*conditions)
            .order_by(Subscription.id)
            .limit(limit)
            .offset(offset)
        )
        return list(rows), total

    @staticmethod
    async def count_seats(db: AsyncSession, subscription_id: int) -> int:
        return await db.scalar(
            select(func.count())
            .select_from(SeatAssignment)
            .where(SeatAssignment.subscription_id == subscription_id)
        )
