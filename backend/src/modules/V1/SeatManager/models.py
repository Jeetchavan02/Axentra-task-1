from sqlalchemy import ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class SeatAssignment(TimestampMixin, Base):
    """One employee holding one seat. Removing a seat deletes the row."""

    __tablename__ = "seat_assignments"
    __table_args__ = (
        UniqueConstraint("subscription_id", "employee_id"),
        # Composite keys: a seat can't link records from two different companies.
        ForeignKeyConstraint(
            ["company_id", "subscription_id"],
            ["subscriptions.company_id", "subscriptions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "employee_id"],
            ["employees.company_id", "employees.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_seat_assignments_company_id_employee_id", "company_id", "employee_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    subscription_id: Mapped[int]
    employee_id: Mapped[int]
