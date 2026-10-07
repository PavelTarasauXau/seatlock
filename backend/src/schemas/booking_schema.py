from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from src.models import BookingStatus
from datetime import datetime

class BookingCreate(BaseModel):
    hold_ids: list[int] = Field(min_length=1)

class BookingItemResponse(BaseModel):
    id: int
    event_seat_id: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: int
    event_id: int
    status: BookingStatus
    total_price: Decimal
    created_at: datetime
    items: list[BookingItemResponse]

    model_config = ConfigDict(from_attributes=True)
