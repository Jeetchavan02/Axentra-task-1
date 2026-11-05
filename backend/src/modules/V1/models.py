"""Imports every model so Base.metadata knows all tables (used by Alembic)."""

from modules.V1.AuthManager.models import Company, User
from modules.V1.EmployeeManager.models import Employee
from modules.V1.SeatManager.models import SeatAssignment
from modules.V1.SubscriptionManager.models import Subscription
from modules.V1.VendorManager.models import Vendor

__all__ = ["Company", "Employee", "SeatAssignment", "Subscription", "User", "Vendor"]
