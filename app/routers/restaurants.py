from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.schemas.restaurant_schema import RestaurantCreate
from app.core.security import get_current_user

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

@router.post("/")
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_restaurant = Restaurant(
        **restaurant.dict(),
        owner_id=current_user.id
    )

    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)

    return new_restaurant

@router.get("/")
def get_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Restaurant).filter(
        Restaurant.owner_id == current_user.id
    ).all()
