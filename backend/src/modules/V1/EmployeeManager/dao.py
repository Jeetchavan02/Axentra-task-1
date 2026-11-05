from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Employee


class EmployeeDAO:
    """Every query filters by company_id, so one company can't reach another's employees."""

    @staticmethod
    async def get(db: AsyncSession, company_id: int, employee_id: int) -> Employee | None:
        return await db.scalar(
            select(Employee).where(Employee.id == employee_id, Employee.company_id == company_id)
        )

    @staticmethod
    async def list(
        db: AsyncSession, company_id: int, limit: int, offset: int, search: str | None
    ) -> tuple[list[Employee], int]:
        conditions = [Employee.company_id == company_id]
        if search:
            conditions.append(
                or_(
                    Employee.full_name.icontains(search, autoescape=True),
                    Employee.email.icontains(search, autoescape=True),
                )
            )
        total = await db.scalar(select(func.count()).select_from(Employee).where(*conditions))
        rows = await db.scalars(
            select(Employee).where(*conditions).order_by(Employee.id).limit(limit).offset(offset)
        )
        return list(rows), total
