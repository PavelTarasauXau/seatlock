from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from src.models import EventSeatStatus

class EventSeatResponse(BaseModel):

    id: int
    seat_id: int
    price: Decimal
    status: EventSeatStatus

    model_config = ConfigDict(from_attributes=True)