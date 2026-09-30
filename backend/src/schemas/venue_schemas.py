from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from datetime import datetime

class VenueCreate(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    address: str = Field(max_length=100)
    layout: dict[str, Any]

class VenueResponse(BaseModel):
    id: int
    name: str
    address: str
    layout: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)