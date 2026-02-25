from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional
from sqlalchemy import desc
from app.models.product_model import Product
from app.models.sale_model import Sale
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.core.exceptions import NotAuthorizedException
from sqlalchemy import cast, Date

def sales_summary_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):

    # Verificar ownership
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise NotAuthorizedException()

    query = db.query(Sale).filter(
        Sale.restaurant_id == restaurant_id
    )

    # Filtros por fecha
    if start_date:
        query = query.filter(Sale.created_at >= start_date)

    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    total_sales = query.count()
    total_revenue = query.with_entities(func.sum(Sale.total)).scalar() or 0
    average_ticket = query.with_entities(func.avg(Sale.total)).scalar() or 0

    return {
        "total_sales": total_sales,
        "total_revenue": float(total_revenue),
        "average_ticket": round(float(average_ticket), 2)
    }



def top_products_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    limit: int = 5
):

    # Verificar ownership
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise NotAuthorizedException()

    results = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(Sale.quantity).label("total_quantity_sold"),
            func.sum(Sale.total).label("total_revenue")
        )
        .join(Sale, Sale.product_id == Product.id)
        .filter(Sale.restaurant_id == restaurant_id)
        .group_by(Product.id, Product.name)
        .order_by(desc(func.sum(Sale.quantity)))
        .limit(limit)
        .all()
    )

    return [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "total_quantity_sold": int(r.total_quantity_sold),
            "total_revenue": float(r.total_revenue)
        }
        for r in results
    ]



def daily_sales_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):

    # Verificar ownership
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise NotAuthorizedException()

    query = db.query(
        cast(Sale.created_at, Date).label("date"),
        func.sum(Sale.total).label("total_revenue"),
        func.sum(Sale.quantity).label("total_items_sold")
    ).filter(
        Sale.restaurant_id == restaurant_id
    )

    if start_date:
        query = query.filter(Sale.created_at >= start_date)

    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    results = (
        query.group_by(cast(Sale.created_at, Date))
        .order_by(cast(Sale.created_at, Date))
        .all()
    )

    return [
        {
            "date": str(r.date),
            "total_revenue": float(r.total_revenue),
            "total_items_sold": int(r.total_items_sold)
        }
        for r in results
    ]

def dashboard_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 5
):
    return {
        "summary": sales_summary_service(
            db, restaurant_id, current_user, start_date, end_date
        ),
        "top_products": top_products_service(
            db, restaurant_id, current_user, limit
        ),
        "daily_sales": daily_sales_service(
            db, restaurant_id, current_user, start_date, end_date
        )
    }
