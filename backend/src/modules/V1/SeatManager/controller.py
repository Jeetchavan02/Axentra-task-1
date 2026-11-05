from sqlalchemy.ext.asyncio import AsyncSession

from app.project_schemas import APIResponse, Page
from modules.V1.EmployeeManager.models import Employee

from .models import SeatAssignment
from .schemas import SeatCreate, SeatRead
from .services import SeatService


def _to_read(seat: SeatAssignment, employee: Employee) -> SeatRead:
    return SeatRead(
        id=seat.id,
        subscription_id=seat.subscription_id,
        employee_id=seat.employee_id,
        employee_name=employee.full_name,
        employee_email=employee.email,
        assigned_at=seat.created_at,
    )


async def assign_seat_controller(
    db: AsyncSession, company_id: int, subscription_id: int, payload: SeatCreate
) -> APIResponse[SeatRead]:
    seat, employee = await SeatService.assign(db, company_id, subscription_id, payload.employee_id)
    return APIResponse[SeatRead].success(
        data=_to_read(seat, employee), message="Seat assigned", code=201
    )


async def list_seats_controller(
    db: AsyncSession, company_id: int, subscription_id: int, limit: int, offset: int
) -> APIResponse[Page[SeatRead]]:
    rows, total = await SeatService.list(db, company_id, subscription_id, limit, offset)
    page = Page[SeatRead](
        items=[_to_read(seat, employee) for seat, employee in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
    return APIResponse[Page[SeatRead]].success(data=page)


async def remove_seat_controller(
    db: AsyncSession, company_id: int, subscription_id: int, employee_id: int
) -> APIResponse[dict[str, int]]:
    await SeatService.remove(db, company_id, subscription_id, employee_id)
    return APIResponse[dict[str, int]].success(
        data={"subscription_id": subscription_id, "employee_id": employee_id},
        message="Seat removed",
    )
