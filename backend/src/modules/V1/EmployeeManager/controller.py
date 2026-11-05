from sqlalchemy.ext.asyncio import AsyncSession

from app.project_schemas import APIResponse, Page

from .dao import EmployeeDAO
from .schemas import EmployeeRead, EmployeeWrite
from .services import EmployeeService


async def create_employee_controller(
    db: AsyncSession, company_id: int, payload: EmployeeWrite
) -> APIResponse[EmployeeRead]:
    employee = await EmployeeService.create(db, company_id, payload)
    return APIResponse[EmployeeRead].success(
        data=EmployeeRead.model_validate(employee), message="Employee created", code=201
    )


async def list_employees_controller(
    db: AsyncSession, company_id: int, limit: int, offset: int, search: str | None
) -> APIResponse[Page[EmployeeRead]]:
    employees, total = await EmployeeDAO.list(db, company_id, limit, offset, search)
    page = Page[EmployeeRead](
        items=[EmployeeRead.model_validate(v) for v in employees],
        total=total,
        limit=limit,
        offset=offset,
    )
    return APIResponse[Page[EmployeeRead]].success(data=page)


async def get_employee_controller(
    db: AsyncSession, company_id: int, employee_id: int
) -> APIResponse[EmployeeRead]:
    employee = await EmployeeService.get(db, company_id, employee_id)
    return APIResponse[EmployeeRead].success(data=EmployeeRead.model_validate(employee))


async def update_employee_controller(
    db: AsyncSession, company_id: int, employee_id: int, payload: EmployeeWrite
) -> APIResponse[EmployeeRead]:
    employee = await EmployeeService.update(db, company_id, employee_id, payload)
    return APIResponse[EmployeeRead].success(
        data=EmployeeRead.model_validate(employee), message="Employee updated"
    )


async def delete_employee_controller(
    db: AsyncSession, company_id: int, employee_id: int
) -> APIResponse[dict[str, int]]:
    await EmployeeService.delete(db, company_id, employee_id)
    return APIResponse[dict[str, int]].success(data={"id": employee_id}, message="Employee deleted")
