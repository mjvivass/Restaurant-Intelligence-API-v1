from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, func
from typing import Optional
from app.services.product_service import create_product_service

from app.db.session import get_db
from app.models.product_model import Product
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.schemas.product_schema import ProductCreate
from app.core.security import get_current_user


router = APIRouter(prefix="/products", tags=["Products"])


# =========================
# CREAR PRODUCTO
# =========================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, func
from typing import Optional

from app.db.session import get_db
from app.models.product_model import Product
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.schemas.product_schema import ProductCreate, ProductResponse
from app.core.security import get_current_user
from datetime import datetime


router = APIRouter(prefix="/products", tags=["Products"])


# =========================
# CREAR PRODUCTO
# =========================

@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_product_service(db, product, current_user)
# =========================
# LISTAR PRODUCTOS
# =========================
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
    current_user: User = Depends(get_current_user)
):

    query = db.query(Product).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id
    )

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


# =========================
# ESTADÍSTICAS
# =========================
@router.get("/stats")
def product_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    query = db.query(Product).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id
    )

    total_products = query.count()
    average_price = query.with_entities(func.avg(Product.price)).scalar() or 0
    min_price = query.with_entities(func.min(Product.price)).scalar() or 0
    max_price = query.with_entities(func.max(Product.price)).scalar() or 0
    total_inventory_value = query.with_entities(func.sum(Product.price * Product.stock)).scalar() or 0

    return {
        "total_products": total_products,
        "average_price": round(float(average_price), 2),
        "min_price": float(min_price),
        "max_price": float(max_price),
        "total_inventory_value": float(total_inventory_value)
    }


# =========================
# PRODUCTOS CON BAJO STOCK (AUTOMATIZACIÓN)
# =========================
@router.get("/low-stock")
def get_low_stock_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    products = db.query(Product).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Product.stock <= Product.min_stock
    ).all()

    return {
        "low_stock_count": len(products),
        "products": products
    }
