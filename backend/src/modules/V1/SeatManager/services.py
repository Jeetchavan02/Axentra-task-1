from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import commit_or_conflict
from modules.V1.EmployeeManager.dao import EmployeeDAO
from modules.V1.EmployeeManager.models import Employee
from modules.V1.SubscriptionManager.dao import SubscriptionDAO
from modules.V1.SubscriptionManager.models import SubscriptionStatus
from modules.V1.SubscriptionManager.services import SubscriptionService

from .dao import SeatDAO
from .models import SeatAssignment


class SeatService:
    @staticmethod
    async def assign(
        db: AsyncSession, company_id: int, subscription_id: int, employee_id: int
    ) -> tuple[SeatAssignment, Employee]:
        # The row lock makes simultaneous requests take turns. Without it, two requests could
        # both count one free seat and both take it. It is released by commit or rollback.
        subscription = await SubscriptionDAO.get(db, company_id, subscription_id, lock=True)
        if subscription is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found")
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(status.HTTP_409_CONFLICT, "Subscription is not active")

        employee = await EmployeeDAO.get(db, company_id, employee_id)
        if employee is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
        if await SeatDAO.get(db, company_id, subscription_id, employee_id):
            raise HTTPException(status.HTTP_409_CONFLICT, "Employee already has this seat")

        seats_in_use = await SubscriptionDAO.count_seats(db, subscription_id)
        if seats_in_use >= subscription.seat_limit:
            raise HTTPException(status.HTTP_409_CONFLICT, "No seats available on this plan")

        seat = SeatAssignment(
            company_id=company_id, subscription_id=subscription_id, employee_id=employee_id
        )
        db.add(seat)
        await commit_or_conflict(db, "Seat could not be assigned")
        return seat, employee

    @staticmethod
    async def list(
        db: AsyncSession, company_id: int, subscription_id: int, limit: int, offset: int
    ) -> tuple[list[tuple[SeatAssignment, Employee]], int]:
        await SubscriptionService.get(db, company_id, subscription_id)
        return await SeatDAO.list(db, company_id, subscription_id, limit, offset)

    @staticmethod
    async def remove(
        db: AsyncSession, company_id: int, subscription_id: int, employee_id: int
    ) -> None:
        seat = await SeatDAO.get(db, company_id, subscription_id, employee_id)
        if seat is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Seat not found")
        await db.delete(seat)
        await db.commit()
