from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.product_model import Product
from app.models.sale_model import Sale
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.core.exceptions import NotAuthorizedException


# =========================
# VALIDACIÓN
# =========================
def validate_access(db, restaurant_id, current_user):
    if current_user.role == "admin":
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == restaurant_id
        ).first()
    else:
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == restaurant_id,
            Restaurant.owner_id == current_user.id
        ).first()

    if not restaurant:
        raise NotAuthorizedException()

    return restaurant


# =========================
# ALERTAS INTELIGENTES
# =========================
def smart_alerts_service(db: Session, restaurant_id: int, current_user: User):

    validate_access(db, restaurant_id, current_user)

    alerts = []

    # 🔥 1. STOCK BAJO
    low_stock_products = db.query(Product).filter(
        Product.restaurant_id == restaurant_id,
        Product.stock <= Product.min_stock
    ).all()

    for p in low_stock_products:
        alerts.append({
            "type": "low_stock",
            "message": f"El producto '{p.name}' tiene stock bajo ({p.stock})"
        })

    # 🔥 2. PRODUCTOS SIN VENTAS (últimos 7 días)
    last_7_days = datetime.utcnow() - timedelta(days=7)

    inactive_products = db.query(Product).filter(
        Product.restaurant_id == restaurant_id
    ).all()

    for p in inactive_products:
        sales_count = db.query(Sale).filter(
            Sale.product_id == p.id,
            Sale.created_at >= last_7_days
        ).count()

        if sales_count == 0:
            alerts.append({
                "type": "no_sales",
                "message": f"El producto '{p.name}' no tuvo ventas en 7 días"
            })

    return alerts


# =========================
# TOP INSIGHTS
# =========================
def smart_insights_service(db: Session, restaurant_id: int, current_user: User):

    validate_access(db, restaurant_id, current_user)

    insights = []

    # 🔥 TOP PRODUCTO
    top_product = db.query(
        Product.name,
        func.sum(Sale.quantity).label("total")
    ).join(Sale).filter(
        Sale.restaurant_id == restaurant_id
    ).group_by(Product.name).order_by(
        func.sum(Sale.quantity).desc()
    ).first()

    if top_product:
        insights.append({
            "type": "top_product",
            "message": f"Tu producto más vendido es '{top_product.name}' con {int(top_product.total)} unidades"
        })

    # 🔥 INGRESOS ÚLTIMOS 7 DÍAS
    last_7_days = datetime.utcnow() - timedelta(days=7)

    revenue = db.query(func.sum(Sale.total)).filter(
        Sale.restaurant_id == restaurant_id,
        Sale.created_at >= last_7_days
    ).scalar() or 0

    insights.append({
        "type": "weekly_revenue",
        "message": f"Ingresos últimos 7 días: ${round(float(revenue), 2)}"
    })

    return insights


# =========================
# PREDICCIÓN SIMPLE (VENTAS)
# =========================
def sales_prediction_service(db: Session, restaurant_id: int, current_user: User):

    validate_access(db, restaurant_id, current_user)

    last_7_days = datetime.utcnow() - timedelta(days=7)

    avg_daily_sales = db.query(
        func.avg(Sale.total)
    ).filter(
        Sale.restaurant_id == restaurant_id,
        Sale.created_at >= last_7_days
    ).scalar() or 0

    predicted_week = avg_daily_sales * 7

    return {
        "avg_daily_sales": round(float(avg_daily_sales), 2),
        "predicted_next_7_days": round(float(predicted_week), 2)
    }