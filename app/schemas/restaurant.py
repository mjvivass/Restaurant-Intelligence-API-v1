from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class RestaurantBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantResponse(RestaurantBase):
    id: int
    created_at: datetime
    active: bool

    class Config:
        from_attributes = True
