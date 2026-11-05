from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.V1.EmployeeManager.models import Employee

from .models import SeatAssignment


class SeatDAO:
    @staticmethod
    async def get(
        db: AsyncSession, company_id: int, subscription_id: int, employee_id: int
    ) -> SeatAssignment | None:
        return await db.scalar(
            select(SeatAssignment).where(
                SeatAssignment.company_id == company_id,
                SeatAssignment.subscription_id == subscription_id,
                SeatAssignment.employee_id == employee_id,
            )
        )

    @staticmethod
    async def list(
        db: AsyncSession, company_id: int, subscription_id: int, limit: int, offset: int
    ) -> tuple[list[tuple[SeatAssignment, Employee]], int]:
        conditions = [
            SeatAssignment.company_id == company_id,
            SeatAssignment.subscription_id == subscription_id,
        ]
        total = await db.scalar(select(func.count()).select_from(SeatAssignment).where(*conditions))
        rows = await db.execute(
            select(SeatAssignment, Employee)
            .join(Employee, Employee.id == SeatAssignment.employee_id)
            .where(*conditions)
            .order_by(SeatAssignment.id)
            .limit(limit)
            .offset(offset)
        )
        return [(seat, employee) for seat, employee in rows], total
