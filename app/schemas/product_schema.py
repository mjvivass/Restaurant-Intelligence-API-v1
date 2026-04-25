from pydantic import BaseModel
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    min_stock: int
    restaurant_id: int


class ProductUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    min_stock: int


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    min_stock: int
    restaurant_id: int

    class Config:
        from_attributes = True