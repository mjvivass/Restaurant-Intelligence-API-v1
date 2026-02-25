from sqlalchemy.orm import Session
from datetime import datetime

from app.models.product_model import Product
from app.models.sale_model import Sale
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.schemas.sale_schema import SaleCreate
from app.core.exceptions import (
    NotAuthorizedException,
    ProductNotFoundException,
    InsufficientStockException
)


def create_sale_service(
    db: Session,
    sale_data: SaleCreate,
    current_user: User
) -> Sale:

    # Verificar restaurante
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == sale_data.restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise NotAuthorizedException()

    # Verificar producto
    product = db.query(Product).filter(
        Product.id == sale_data.product_id,
        Product.restaurant_id == sale_data.restaurant_id
    ).first()

    if not product:
        raise ProductNotFoundException()

    # Verificar stock
    if product.stock < sale_data.quantity:
        raise InsufficientStockException()

    # Calcular total
    total = product.price * sale_data.quantity

    # Descontar inventario
    product.stock -= sale_data.quantity
    product.last_updated = datetime.utcnow()

    # Crear venta
    new_sale = Sale(
        restaurant_id=sale_data.restaurant_id,
        product_id=sale_data.product_id,
        quantity=sale_data.quantity,
        unit_price=product.price,
        total=total
    )

    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    return new_sale