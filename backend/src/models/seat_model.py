import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

if TYPE_CHECKING:
    from src.models.venue_model import Venue


class SeatType(str, enum.Enum):
    STANDARD = "standard"
    VIP = "vip"

class Seat(Base):
    __tablename__ = "seats"

    __table_args__ = (
        UniqueConstraint("venue_id", "section", "row_number", "seat_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="RESTRICT"), index=True
    )
    section: Mapped[str] = mapped_column(String(20))
    row_number: Mapped[int] = mapped_column(Integer)
    seat_number: Mapped[int] = mapped_column(Integer)
    
    seat_type: Mapped[SeatType] = mapped_column(
        Enum(SeatType, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=SeatType.STANDARD
    )

    venue: Mapped["Venue"] = relationship(back_populates="seats")
