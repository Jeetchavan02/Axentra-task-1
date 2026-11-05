from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.V1.SubscriptionManager.models import BillingCycle, Subscription, SubscriptionStatus
from modules.V1.VendorManager.models import Vendor


class ReportDAO:
    """Reports count active subscriptions only, always within one company."""

    @staticmethod
    async def upcoming_renewals(
        db: AsyncSession, company_id: int, start: date, end: date, limit: int, offset: int
    ) -> tuple[list[tuple[Subscription, str]], int]:
        conditions = [
            Subscription.company_id == company_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.renewal_date.between(start, end),
        ]
        total = await db.scalar(select(func.count()).select_from(Subscription).where(*conditions))
        rows = await db.execute(
            select(Subscription, Vendor.name)
            .join(Vendor, Vendor.id == Subscription.vendor_id)
            .where(*conditions)
            .order_by(Subscription.renewal_date, Subscription.id)
            .limit(limit)
            .offset(offset)
        )
        return [(subscription, name) for subscription, name in rows], total

    @staticmethod
    async def spend_by_vendor(
        db: AsyncSession, company_id: int
    ) -> list[tuple[int, str, Decimal, int]]:
        # Yearly plans count as one twelfth of their price per month.
        monthly_price = case(
            (Subscription.billing_cycle == BillingCycle.YEARLY, Subscription.price / 12),
            else_=Subscription.price,
        )
        rows = await db.execute(
            select(Vendor.id, Vendor.name, func.sum(monthly_price), func.count())
            .join(Subscription, Subscription.vendor_id == Vendor.id)
            .where(
                Subscription.company_id == company_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .group_by(Vendor.id, Vendor.name)
            .order_by(Vendor.name)
        )
        return [tuple(row) for row in rows]
