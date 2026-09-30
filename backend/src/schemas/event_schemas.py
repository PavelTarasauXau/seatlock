from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from src.models.event_model import EventStatus

class EventCreate(BaseModel):

    venue_id: int
    title: str = Field(max_length=100)
    starts_at: datetime

class EventResponse(BaseModel):

    id: int
    venue_id: int
    title: str
    starts_at: datetime
    status: EventStatus
    hold_ttl_seconds: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)