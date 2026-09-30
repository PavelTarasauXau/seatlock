from pydantic import BaseModel, Field, ConfigDict
from src.models.seat_model import SeatType

class SeatCreate(BaseModel):

    section: str = Field(max_length=20)
    row_number: int = Field(gt = 0)
    seat_number: int = Field(gt = 0)
    seat_type: SeatType = SeatType.STANDARD

class SeatResponse(BaseModel):

    id: int
    venue_id: int
    section: str
    row_number: int
    seat_number: int
    seat_type: SeatType 

    model_config = ConfigDict(from_attributes=True)
