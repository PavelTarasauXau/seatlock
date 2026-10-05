from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.hold_model import HoldStatus


class HoldResponse(BaseModel):

    id: int
    event_seat_id: int
    user_id: int
    status: HoldStatus
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
