from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


def _string_enum(enum_class: type[StrEnum], name: str) -> Enum:
    # Stored as checked text, so adding a value later doesn't require altering a database type.
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda members: [member.value for member in members],
    )


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("company_id", "vendor_id", "plan_name"),
        UniqueConstraint("company_id", "id"),
        ForeignKeyConstraint(
            ["company_id", "vendor_id"],
            ["vendors.company_id", "vendors.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("price >= 0", name="price_not_negative"),
        CheckConstraint("seat_limit >= 1", name="seat_limit_positive"),
        Index("ix_subscriptions_company_id_renewal_date", "company_id", "renewal_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    vendor_id: Mapped[int]
    plan_name: Mapped[str] = mapped_column(String(255))
    # Numeric, not float: floats can't represent money exactly. Price is per billing cycle.
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    billing_cycle: Mapped[BillingCycle] = mapped_column(_string_enum(BillingCycle, "billing_cycle"))
    seat_limit: Mapped[int]
    renewal_date: Mapped[date] = mapped_column(Date)
    status: Mapped[SubscriptionStatus] = mapped_column(
        _string_enum(SubscriptionStatus, "status"), default=SubscriptionStatus.ACTIVE
    )
