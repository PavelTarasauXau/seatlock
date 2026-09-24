from pydantic import BaseModel, Field, EmailStr, ConfigDict

class UserCreate(BaseModel):
    username: str = Field(min_length=5, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)