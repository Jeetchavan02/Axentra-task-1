from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.project_schemas import POSTGRES_INT_MAX, Name

from .models import BillingCycle, SubscriptionStatus


class SubscriptionWrite(BaseModel):
    """Used for create and full update. company_id is rejected: it only comes from the token."""

    model_config = ConfigDict(extra="forbid")

    vendor_id: int = Field(gt=0, le=POSTGRES_INT_MAX)
    plan_name: Name
    # Matches Numeric(10, 2). Price is per billing cycle.
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    billing_cycle: BillingCycle
    seat_limit: int = Field(ge=1, le=POSTGRES_INT_MAX)
    renewal_date: date
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    plan_name: str
    price: Decimal  # Sent as a JSON string, so clients don't lose exactness.
    billing_cycle: BillingCycle
    seat_limit: int
    renewal_date: date
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime
