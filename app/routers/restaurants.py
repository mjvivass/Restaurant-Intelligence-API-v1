from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.schemas.restaurant_schema import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
)
from app.core.security import require_employee

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


# =========================
# CREATE RESTAURANT
# =========================
@router.post("/", response_model=RestaurantResponse)
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    new_restaurant = Restaurant(
        **restaurant.dict(),
        owner_id=current_user.id
    )

    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)

    return new_restaurant


# =========================
# GET MY RESTAURANTS
# =========================
@router.get("/", response_model=list[RestaurantResponse])
def get_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return db.query(Restaurant).filter(
        Restaurant.owner_id == current_user.id
    ).all()


# =========================
# GET RESTAURANT BY ID
# =========================
@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return restaurant


# =========================
# UPDATE RESTAURANT
# =========================
@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    update_data = restaurant_data.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se enviaron campos para actualizar"
        )

    for field, value in update_data.items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)

    return restaurant