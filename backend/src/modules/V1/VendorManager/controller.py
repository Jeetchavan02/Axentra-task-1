from sqlalchemy.ext.asyncio import AsyncSession

from app.project_schemas import APIResponse, Page

from .dao import VendorDAO
from .schemas import VendorRead, VendorWrite
from .services import VendorService


async def create_vendor_controller(
    db: AsyncSession, company_id: int, payload: VendorWrite
) -> APIResponse[VendorRead]:
    vendor = await VendorService.create(db, company_id, payload)
    return APIResponse[VendorRead].success(
        data=VendorRead.model_validate(vendor), message="Vendor created", code=201
    )


async def list_vendors_controller(
    db: AsyncSession, company_id: int, limit: int, offset: int, search: str | None
) -> APIResponse[Page[VendorRead]]:
    vendors, total = await VendorDAO.list(db, company_id, limit, offset, search)
    page = Page[VendorRead](
        items=[VendorRead.model_validate(v) for v in vendors],
        total=total,
        limit=limit,
        offset=offset,
    )
    return APIResponse[Page[VendorRead]].success(data=page)


async def get_vendor_controller(
    db: AsyncSession, company_id: int, vendor_id: int
) -> APIResponse[VendorRead]:
    vendor = await VendorService.get(db, company_id, vendor_id)
    return APIResponse[VendorRead].success(data=VendorRead.model_validate(vendor))


async def update_vendor_controller(
    db: AsyncSession, company_id: int, vendor_id: int, payload: VendorWrite
) -> APIResponse[VendorRead]:
    vendor = await VendorService.update(db, company_id, vendor_id, payload)
    return APIResponse[VendorRead].success(
        data=VendorRead.model_validate(vendor), message="Vendor updated"
    )


async def delete_vendor_controller(
    db: AsyncSession, company_id: int, vendor_id: int
) -> APIResponse[dict[str, int]]:
    await VendorService.delete(db, company_id, vendor_id)
    return APIResponse[dict[str, int]].success(data={"id": vendor_id}, message="Vendor deleted")
