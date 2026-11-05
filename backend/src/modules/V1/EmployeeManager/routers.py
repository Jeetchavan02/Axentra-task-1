from fastapi import APIRouter, status

from app.database import DbSession
from app.project_schemas import APIResponse, Limit, Offset, Page, ResourceId, Search
from modules.V1.AuthManager.dependencies import CurrentUser

from . import api_docs, controller
from .schemas import EmployeeRead, EmployeeWrite

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, **api_docs.CREATE)
async def create_employee(
    db: DbSession, user: CurrentUser, payload: EmployeeWrite
) -> APIResponse[EmployeeRead]:
    return await controller.create_employee_controller(db, user.company_id, payload)


@router.get("", **api_docs.LIST)
async def list_employees(
    db: DbSession, user: CurrentUser, limit: Limit = 20, offset: Offset = 0, search: Search = None
) -> APIResponse[Page[EmployeeRead]]:
    return await controller.list_employees_controller(db, user.company_id, limit, offset, search)


@router.get("/{employee_id}", **api_docs.GET)
async def get_employee(
    db: DbSession, user: CurrentUser, employee_id: ResourceId
) -> APIResponse[EmployeeRead]:
    return await controller.get_employee_controller(db, user.company_id, employee_id)


@router.put("/{employee_id}", **api_docs.UPDATE)
async def update_employee(
    db: DbSession, user: CurrentUser, employee_id: ResourceId, payload: EmployeeWrite
) -> APIResponse[EmployeeRead]:
    return await controller.update_employee_controller(db, user.company_id, employee_id, payload)


@router.delete("/{employee_id}", **api_docs.DELETE)
async def delete_employee(
    db: DbSession, user: CurrentUser, employee_id: ResourceId
) -> APIResponse[dict[str, int]]:
    return await controller.delete_employee_controller(db, user.company_id, employee_id)
