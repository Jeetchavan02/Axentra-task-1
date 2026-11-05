from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from modules.V1.SubscriptionManager.models import BillingCycle


class RenewalRead(BaseModel):
    subscription_id: int
    vendor_name: str
    plan_name: str
    price: Decimal
    billing_cycle: BillingCycle
    renewal_date: date
    days_until_renewal: int


class VendorSpend(BaseModel):
    vendor_id: int
    vendor_name: str
    monthly_spend: Decimal


class MonthlySpendRead(BaseModel):
    total_monthly_spend: Decimal
    active_subscriptions: int
    by_vendor: list[VendorSpend]
