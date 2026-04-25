from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.product_model import Product
from app.models.restaurant_model import Restaurant


def create_product_service(db: Session, product_data, current_user):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == product_data.restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=403,
            detail="Este restaurante no te pertenece o no existe"
        )

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


def update_product_service(db: Session, product_id: int, product_data, current_user):
    product = (
        db.query(Product)
        .join(Restaurant, Product.restaurant_id == Restaurant.id)
        .filter(
            Product.id == product_id,
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    product.name = product_data.name
    product.description = product_data.description
    product.price = product_data.price
    product.stock = product_data.stock
    product.min_stock = product_data.min_stock
    product.last_updated = datetime.utcnow()

    db.commit()
    db.refresh(product)

    return product


def delete_product_service(db: Session, product_id: int, current_user):
    product = (
        db.query(Product)
        .join(Restaurant, Product.restaurant_id == Restaurant.id)
        .filter(
            Product.id == product_id,
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(product)
    db.commit()

    return {"message": "Producto eliminado correctamente"}