from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, func
from typing import Optional

from app.db.session import get_db
from app.models.product_model import Product
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.schemas.product_schema import ProductCreate, ProductResponse, ProductUpdate
from app.core.security import require_employee, require_manager
from app.services.product_service import (
    create_product_service,
    update_product_service,
    delete_product_service
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return create_product_service(db, product, current_user)


@router.get("/")
def get_products(
    skip: int = 0,
    limit: int = 10,
    name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    order_by: Optional[str] = "id",
    order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    owned_restaurants = db.query(Restaurant.id).filter(
        Restaurant.owner_id == current_user.id
    ).all()

    restaurant_ids = [r.id for r in owned_restaurants]

    if not restaurant_ids:
        raise HTTPException(status_code=403, detail="Debes crear un restaurante primero")

    query = db.query(Product).filter(Product.restaurant_id.in_(restaurant_ids))

    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    total = query.count()

    if hasattr(Product, order_by):
        column = getattr(Product, order_by)
        query = query.order_by(desc(column) if order == "desc" else asc(column))

    items = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items
    }


@router.get("/stats")
def product_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    owned_restaurants = db.query(Restaurant.id).filter(
        Restaurant.owner_id == current_user.id
    ).all()

    restaurant_ids = [r.id for r in owned_restaurants]

    if not restaurant_ids:
        raise HTTPException(status_code=403, detail="Debes crear un restaurante primero")

    query = db.query(Product).filter(Product.restaurant_id.in_(restaurant_ids))

    total_products = query.count()
    average_price = query.with_entities(func.avg(Product.price)).scalar() or 0
    min_price = query.with_entities(func.min(Product.price)).scalar() or 0
    max_price = query.with_entities(func.max(Product.price)).scalar() or 0
    total_inventory_value = query.with_entities(
        func.sum(Product.price * Product.stock)
    ).scalar() or 0

    return {
        "total_products": total_products,
        "average_price": round(float(average_price), 2),
        "min_price": float(min_price),
        "max_price": float(max_price),
        "total_inventory_value": float(total_inventory_value)
    }


@router.get("/low-stock")
def get_low_stock_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    owned_restaurants = db.query(Restaurant.id).filter(
        Restaurant.owner_id == current_user.id
    ).all()

    restaurant_ids = [r.id for r in owned_restaurants]

    if not restaurant_ids:
        raise HTTPException(status_code=403, detail="Debes crear un restaurante primero")

    products = db.query(Product).filter(
        Product.restaurant_id.in_(restaurant_ids),
        Product.stock <= Product.min_stock
    ).all()

    return {
        "low_stock_count": len(products),
        "products": products
    }


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return update_product_service(db, product_id, product, current_user)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return delete_product_service(db, product_id, current_user)