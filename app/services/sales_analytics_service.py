from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, cast, Date
from datetime import datetime
from typing import Optional

from app.models.sale_model import Sale, SaleDetail, SalePayment
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.core.exceptions import NotAuthorizedException


def validate_restaurant_access(db: Session, restaurant_id: int, current_user: User):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise NotAuthorizedException()

    return restaurant


def _build_sales_base_query(
    db: Session,
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    query = db.query(Sale).filter(
        Sale.restaurant_id == restaurant_id,
        Sale.status != "cancelada"
    )

    if start_date:
        query = query.filter(Sale.created_at >= start_date)

    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    return query


def sales_summary_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    validate_restaurant_access(db, restaurant_id, current_user)

    sales_query = _build_sales_base_query(db, restaurant_id, start_date, end_date)

    sales = (
        sales_query
        .options(joinedload(Sale.payments))
        .all()
    )

    total_sales = len(sales)
    total_revenue = float(sum(float(s.total or 0) for s in sales))
    average_ticket = round(total_revenue / total_sales, 2) if total_sales > 0 else 0.0

    total_collected = float(
        sum(
            float(payment.amount or 0)
            for sale in sales
            for payment in sale.payments
        )
    )

    pending_balance = float(
        sum(
            max(float(s.total or 0) - sum(float(p.amount or 0) for p in s.payments), 0)
            for s in sales
        )
    )

    return {
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "average_ticket": average_ticket,
        "total_collected": round(total_collected, 2),
        "pending_balance": round(pending_balance, 2),
    }


def top_products_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    limit: int = 5
):
    validate_restaurant_access(db, restaurant_id, current_user)

    results = (
        db.query(
            SaleDetail.product_id.label("product_id"),
            SaleDetail.product_name.label("product_name"),
            func.sum(SaleDetail.quantity).label("total_quantity_sold"),
            func.sum(SaleDetail.line_total).label("total_revenue")
        )
        .join(Sale, SaleDetail.sale_id == Sale.id)
        .filter(
            Sale.restaurant_id == restaurant_id,
            Sale.status != "cancelada"
        )
        .group_by(SaleDetail.product_id, SaleDetail.product_name)
        .order_by(desc(func.sum(SaleDetail.quantity)))
        .limit(limit)
        .all()
    )

    return [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "total_quantity_sold": int(r.total_quantity_sold or 0),
            "total_revenue": float(r.total_revenue or 0),
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
    validate_restaurant_access(db, restaurant_id, current_user)

    query = db.query(
        cast(Sale.created_at, Date).label("date"),
        func.sum(Sale.total).label("total_revenue"),
        func.count(Sale.id).label("total_sales")
    ).filter(
        Sale.restaurant_id == restaurant_id,
        Sale.status != "cancelada"
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
            "total_revenue": float(r.total_revenue or 0),
            "total_sales": int(r.total_sales or 0),
        }
        for r in results
    ]


def sales_by_payment_method_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    validate_restaurant_access(db, restaurant_id, current_user)

    query = (
        db.query(
            SalePayment.payment_method.label("payment_method"),
            func.sum(SalePayment.amount).label("total_amount")
        )
        .join(Sale, SalePayment.sale_id == Sale.id)
        .filter(
            Sale.restaurant_id == restaurant_id,
            Sale.status != "cancelada"
        )
    )

    if start_date:
        query = query.filter(Sale.created_at >= start_date)

    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    results = (
        query.group_by(SalePayment.payment_method)
        .order_by(desc(func.sum(SalePayment.amount)))
        .all()
    )

    return [
        {
            "payment_method": r.payment_method,
            "total_amount": float(r.total_amount or 0),
        }
        for r in results
    ]


def orders_by_status_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    validate_restaurant_access(db, restaurant_id, current_user)

    query = db.query(
        Sale.status.label("status"),
        func.count(Sale.id).label("total_orders")
    ).filter(
        Sale.restaurant_id == restaurant_id
    )

    if start_date:
        query = query.filter(Sale.created_at >= start_date)

    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    results = (
        query.group_by(Sale.status)
        .order_by(desc(func.count(Sale.id)))
        .all()
    )

    return [
        {
            "status": r.status,
            "total_orders": int(r.total_orders or 0),
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
        ),
        "sales_by_payment_method": sales_by_payment_method_service(
            db, restaurant_id, current_user, start_date, end_date
        ),
        "orders_by_status": orders_by_status_service(
            db, restaurant_id, current_user, start_date, end_date
        ),
    }