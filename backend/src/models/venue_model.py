from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.seat_model import Seat


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(100))
    layout: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # lazy="selectin": места подгружаются отдельным SELECT ... IN (...) автоматически,
    # как только загружен сам Venue — это единственная стратегия ленивой загрузки,
    # которая сама по себе безопасно работает в async SQLAlchemy "из коробки"
    seats: Mapped[list["Seat"]] = relationship(back_populates="venue", lazy="selectin")
