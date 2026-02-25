from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.product_model import Product
from app.models.restaurant_model import Restaurant


def create_product_service(db: Session, product_data, current_user):

    # Verificar que el restaurante pertenece al usuario
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == product_data.restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=403, detail="Not authorized")

    new_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        min_stock=product_data.min_stock,
        restaurant_id=product_data.restaurant_id,
        last_updated=datetime.utcnow()
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product 