from decimal import Decimal
import enum

from datetime import datetime
from src.database import Base
from sqlalchemy import Numeric, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=20), default=PaymentStatus.PENDING
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    provider: Mapped[str] = mapped_column(String(50))
    provider_ref: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

