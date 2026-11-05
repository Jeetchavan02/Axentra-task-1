from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .dao import EmployeeDAO
from .models import Employee
from .schemas import EmployeeWrite

EMAIL_TAKEN = "An employee with this email already exists"


class EmployeeService:
    @staticmethod
    async def get(db: AsyncSession, company_id: int, employee_id: int) -> Employee:
        employee = await EmployeeDAO.get(db, company_id, employee_id)
        if employee is None:
            # Also the answer for another company's employee, so its existence isn't revealed.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
        return employee

    @staticmethod
    async def create(db: AsyncSession, company_id: int, payload: EmployeeWrite) -> Employee:
        employee = Employee(company_id=company_id, **payload.model_dump())
        db.add(employee)
        await _commit_or_conflict(db, EMAIL_TAKEN)
        return employee

    @staticmethod
    async def update(
        db: AsyncSession, company_id: int, employee_id: int, payload: EmployeeWrite
    ) -> Employee:
        employee = await EmployeeService.get(db, company_id, employee_id)
        employee.full_name = payload.full_name
        employee.email = payload.email
        await _commit_or_conflict(db, EMAIL_TAKEN)
        return employee

    @staticmethod
    async def delete(db: AsyncSession, company_id: int, employee_id: int) -> None:
        employee = await EmployeeService.get(db, company_id, employee_id)
        await db.delete(employee)
        await _commit_or_conflict(db, "Employee holds seats and can't be deleted")


async def _commit_or_conflict(db: AsyncSession, message: str) -> None:
    """Database constraints are the final check, which also covers simultaneous requests."""
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, message) from exc
