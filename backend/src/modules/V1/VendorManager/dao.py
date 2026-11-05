from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Vendor


class VendorDAO:
    """Every query filters by company_id, so one company can't reach another's vendors."""

    @staticmethod
    async def get(db: AsyncSession, company_id: int, vendor_id: int) -> Vendor | None:
        return await db.scalar(
            select(Vendor).where(Vendor.id == vendor_id, Vendor.company_id == company_id)
        )

    @staticmethod
    async def list(
        db: AsyncSession, company_id: int, limit: int, offset: int, search: str | None
    ) -> tuple[list[Vendor], int]:
        conditions = [Vendor.company_id == company_id]
        if search:
            # autoescape stops % and _ in user input from acting as wildcards.
            conditions.append(Vendor.name.icontains(search, autoescape=True))
        total = await db.scalar(select(func.count()).select_from(Vendor).where(*conditions))
        rows = await db.scalars(
            select(Vendor).where(*conditions).order_by(Vendor.id).limit(limit).offset(offset)
        )
        return list(rows), total
