from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import commit_or_conflict

from .dao import VendorDAO
from .models import Vendor
from .schemas import VendorWrite


class VendorService:
    @staticmethod
    async def get(db: AsyncSession, company_id: int, vendor_id: int) -> Vendor:
        vendor = await VendorDAO.get(db, company_id, vendor_id)
        if vendor is None:
            # Also the answer for another company's vendor, so its existence isn't revealed.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Vendor not found")
        return vendor

    @staticmethod
    async def create(db: AsyncSession, company_id: int, payload: VendorWrite) -> Vendor:
        vendor = Vendor(company_id=company_id, **payload.model_dump())
        db.add(vendor)
        await commit_or_conflict(db, "A vendor with this name already exists")
        return vendor

    @staticmethod
    async def update(
        db: AsyncSession, company_id: int, vendor_id: int, payload: VendorWrite
    ) -> Vendor:
        vendor = await VendorService.get(db, company_id, vendor_id)
        vendor.name = payload.name
        vendor.website = payload.website
        await commit_or_conflict(db, "A vendor with this name already exists")
        return vendor

    @staticmethod
    async def delete(db: AsyncSession, company_id: int, vendor_id: int) -> None:
        vendor = await VendorService.get(db, company_id, vendor_id)
        await db.delete(vendor)
        await commit_or_conflict(db, "Vendor has subscriptions and can't be deleted")
