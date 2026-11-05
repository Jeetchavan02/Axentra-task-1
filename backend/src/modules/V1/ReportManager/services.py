from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from .dao import ReportDAO
from .schemas import MonthlySpendRead, RenewalRead, VendorSpend

CENTS = Decimal("0.01")


def _to_money(amount: Decimal) -> Decimal:
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


class ReportService:
    @staticmethod
    async def upcoming_renewals(
        db: AsyncSession, company_id: int, days: int, limit: int, offset: int
    ) -> tuple[list[RenewalRead], int]:
        today = datetime.now(UTC).date()
        rows, total = await ReportDAO.upcoming_renewals(
            db, company_id, today, today + timedelta(days=days), limit, offset
        )
        renewals = [
            RenewalRead(
                subscription_id=subscription.id,
                vendor_name=vendor_name,
                plan_name=subscription.plan_name,
                price=subscription.price,
                billing_cycle=subscription.billing_cycle,
                renewal_date=subscription.renewal_date,
                days_until_renewal=(subscription.renewal_date - today).days,
            )
            for subscription, vendor_name in rows
        ]
        return renewals, total

    @staticmethod
    async def monthly_spend(db: AsyncSession, company_id: int) -> MonthlySpendRead:
        rows = await ReportDAO.spend_by_vendor(db, company_id)
        # The total sums exact amounts before rounding, so it can differ from the rounded
        # vendor lines by a cent.
        return MonthlySpendRead(
            total_monthly_spend=_to_money(sum((row[2] for row in rows), Decimal(0))),
            active_subscriptions=sum(row[3] for row in rows),
            by_vendor=[
                VendorSpend(vendor_id=row[0], vendor_name=row[1], monthly_spend=_to_money(row[2]))
                for row in rows
            ],
        )
