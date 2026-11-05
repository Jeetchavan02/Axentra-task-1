from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class Vendor(TimestampMixin, Base):
    __tablename__ = "vendors"
    __table_args__ = (
        UniqueConstraint("company_id", "name"),
        # Target for composite foreign keys that keep child rows inside one company.
        UniqueConstraint("company_id", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(500))
