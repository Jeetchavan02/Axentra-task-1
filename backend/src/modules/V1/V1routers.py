from fastapi import APIRouter

from modules.V1.AuthManager.routers import router as auth_router
from modules.V1.EmployeeManager.routers import router as employee_router
from modules.V1.SeatManager.routers import router as seat_router
from modules.V1.SubscriptionManager.routers import router as subscription_router
from modules.V1.VendorManager.routers import router as vendor_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(vendor_router, prefix="/vendors", tags=["vendors"])
router.include_router(employee_router, prefix="/employees", tags=["employees"])
router.include_router(subscription_router, prefix="/subscriptions", tags=["subscriptions"])
router.include_router(seat_router, prefix="/subscriptions/{subscription_id}/seats", tags=["seats"])
