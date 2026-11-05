from sqlalchemy.ext.asyncio import AsyncSession

from app.project_schemas import APIResponse, Page

from .schemas import MonthlySpendRead, RenewalRead
from .services import ReportService


async def upcoming_renewals_controller(
    db: AsyncSession, company_id: int, days: int, limit: int, offset: int
) -> APIResponse[Page[RenewalRead]]:
    renewals, total = await ReportService.upcoming_renewals(db, company_id, days, limit, offset)
    page = Page[RenewalRead](items=renewals, total=total, limit=limit, offset=offset)
    return APIResponse[Page[RenewalRead]].success(data=page)


async def monthly_spend_controller(
    db: AsyncSession, company_id: int
) -> APIResponse[MonthlySpendRead]:
    report = await ReportService.monthly_spend(db, company_id)
    return APIResponse[MonthlySpendRead].success(data=report)
