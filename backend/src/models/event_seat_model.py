import enum
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Enum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class EventSeatStatus(str, enum.Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"

class EventSeat(Base):
    __tablename__ = "event_seats"

    __table_args__ = (
        UniqueConstraint("event_id", "seat_id"),
        Index("ix_event_seats_event_id_status", "event_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT")
    )
    seat_id: Mapped[int] = mapped_column(
        ForeignKey("seats.id", ondelete="RESTRICT"), index=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[EventSeatStatus] = mapped_column(
        Enum(EventSeatStatus, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=EventSeatStatus.AVAILABLE
    )