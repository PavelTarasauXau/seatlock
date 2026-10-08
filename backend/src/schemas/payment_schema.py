import enum

from pydantic import BaseModel, ConfigDict
from src.models import PaymentStatus
from decimal import Decimal
from datetime import datetime

class WebhookStatus(str, enum.Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    status: PaymentStatus
    amount: Decimal
    provider: str
    provider_ref: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaymentWebhook(BaseModel):
    provider_ref: str
    status: WebhookStatus