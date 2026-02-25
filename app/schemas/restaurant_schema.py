from pydantic import BaseModel

class RestaurantCreate(BaseModel):
    name: str
    address: str
    email: str
    phone: str

class RestaurantResponse(BaseModel):
    id: int
    name: str
    address: str
    email: str
    phone: str

    class Config:
        from_attributes = True 
