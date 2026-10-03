import enum

from datetime import datetime

from sqlalchemy import ForeignKey, Enum, DateTime, func, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class HoldStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CONVERTED = "converted"
    RELEASED = "released"


class Hold(Base):
    __tablename__ = "holds"

    __table_args__ = (
        Index(
            "ix_holds_one_active_per_seat",
            "event_seat_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_seat_id: Mapped[int] = mapped_column(
        ForeignKey("event_seats.id", ondelete="RESTRICT"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[HoldStatus] = mapped_column(
        Enum(HoldStatus, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=HoldStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )