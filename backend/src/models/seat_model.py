import enum

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class SeatType(str, enum.Enum):
    STANDARD = "standard"
    VIP = "vip"
    WHEELCHAIR = "wheelchair"


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
        Enum(SeatType, native_enum=False, length=20), default=SeatType.STANDARD
    )
