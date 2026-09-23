import enum

from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func, Enum
from src.database import Base
from sqlalchemy.orm import Mapped, mapped_column

class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    ON_SALE = "on_sale"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(100))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, native_enum = False, length = 20), default=EventStatus.DRAFT
    )

    hold_ttl_seconds: Mapped[int] = mapped_column(default=600)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
