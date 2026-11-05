from fastapi import APIRouter, status

from app.database import DbSession
from app.project_schemas import APIResponse, Limit, Offset, Page, ResourceId, Search
from modules.V1.AuthManager.dependencies import CurrentUser

from . import api_docs, controller
from .schemas import VendorRead, VendorWrite

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, **api_docs.CREATE)
async def create_vendor(
    db: DbSession, user: CurrentUser, payload: VendorWrite
) -> APIResponse[VendorRead]:
    return await controller.create_vendor_controller(db, user.company_id, payload)


@router.get("", **api_docs.LIST)
async def list_vendors(
    db: DbSession, user: CurrentUser, limit: Limit = 20, offset: Offset = 0, search: Search = None
) -> APIResponse[Page[VendorRead]]:
    return await controller.list_vendors_controller(db, user.company_id, limit, offset, search)


@router.get("/{vendor_id}", **api_docs.GET)
async def get_vendor(
    db: DbSession, user: CurrentUser, vendor_id: ResourceId
) -> APIResponse[VendorRead]:
    return await controller.get_vendor_controller(db, user.company_id, vendor_id)


@router.put("/{vendor_id}", **api_docs.UPDATE)
async def update_vendor(
    db: DbSession, user: CurrentUser, vendor_id: ResourceId, payload: VendorWrite
) -> APIResponse[VendorRead]:
    return await controller.update_vendor_controller(db, user.company_id, vendor_id, payload)


@router.delete("/{vendor_id}", **api_docs.DELETE)
async def delete_vendor(
    db: DbSession, user: CurrentUser, vendor_id: ResourceId
) -> APIResponse[dict[str, int]]:
    return await controller.delete_vendor_controller(db, user.company_id, vendor_id)
