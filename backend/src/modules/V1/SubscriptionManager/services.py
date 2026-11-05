from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import commit_or_conflict
from modules.V1.VendorManager.dao import VendorDAO

from .dao import SubscriptionDAO
from .models import Subscription
from .schemas import SubscriptionWrite

DUPLICATE_PLAN = "This vendor already has a subscription with this plan"


class SubscriptionService:
    @staticmethod
    async def get(db: AsyncSession, company_id: int, subscription_id: int) -> Subscription:
        subscription = await SubscriptionDAO.get(db, company_id, subscription_id)
        if subscription is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found")
        return subscription

    @staticmethod
    async def _require_vendor(db: AsyncSession, company_id: int, vendor_id: int) -> None:
        # Same answer for another company's vendor, so its existence isn't revealed.
        if await VendorDAO.get(db, company_id, vendor_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Vendor not found")

    @staticmethod
    async def create(db: AsyncSession, company_id: int, payload: SubscriptionWrite) -> Subscription:
        await SubscriptionService._require_vendor(db, company_id, payload.vendor_id)
        subscription = Subscription(company_id=company_id, **payload.model_dump())
        db.add(subscription)
        await commit_or_conflict(db, DUPLICATE_PLAN)
        return subscription

    @staticmethod
    async def update(
        db: AsyncSession, company_id: int, subscription_id: int, payload: SubscriptionWrite
    ) -> Subscription:
        # Locked so a seat can't be assigned between the check below and the commit.
        subscription = await SubscriptionDAO.get(db, company_id, subscription_id, lock=True)
        if subscription is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found")
        await SubscriptionService._require_vendor(db, company_id, payload.vendor_id)
        seats_in_use = await SubscriptionDAO.count_seats(db, subscription_id)
        if payload.seat_limit < seats_in_use:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Seat limit can't be below the {seats_in_use} seats in use",
            )
        for field, value in payload.model_dump().items():
            setattr(subscription, field, value)
        await commit_or_conflict(db, DUPLICATE_PLAN)
        return subscription

    @staticmethod
    async def delete(db: AsyncSession, company_id: int, subscription_id: int) -> None:
        subscription = await SubscriptionService.get(db, company_id, subscription_id)
        await db.delete(subscription)
        await commit_or_conflict(db, "Subscription has active seats and can't be deleted")
