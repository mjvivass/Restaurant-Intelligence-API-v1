from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.services.sales_analytics_service import (
    sales_summary_service,
    top_products_service,
    daily_sales_service,
    dashboard_service
)
from app.services.sale_service import (
    create_sale_service,
    open_cash_session_service,
    get_current_cash_session_service,
    close_cash_session_service,
    get_sales_service,
    update_sale_status_service,
    add_product_to_sale_service,
    add_payment_to_sale_service
)
from app.db.session import get_db
from app.models.user_model import User
from app.models.sale_model import Sale
from app.schemas.sale_schema import (
    SaleCreate,
    SaleResponse,
    CashOpenCreate,
    CashCloseCreate,
    CashSessionResponse,
    AddPaymentRequest
)
from app.core.security import require_employee

router = APIRouter(prefix="/sales", tags=["Sales"])


# =========================
# CAJA
# =========================
@router.post("/cash/open", response_model=CashSessionResponse)
def open_cash_session(
    cash_data: CashOpenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return open_cash_session_service(db, cash_data, current_user)


@router.get("/cash/current", response_model=CashSessionResponse)
def get_current_cash_session(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return get_current_cash_session_service(db, restaurant_id, current_user)


@router.post("/cash/{cash_session_id}/close")
def close_cash_session(
    cash_session_id: int,
    close_data: CashCloseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return close_cash_session_service(db, cash_session_id, close_data, current_user)


# =========================
# CREAR VENTA / ORDEN
# =========================
@router.post("/", response_model=SaleResponse)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return create_sale_service(db, sale, current_user)


# =========================
# LISTAR VENTAS / ÓRDENES
# =========================
@router.get("/")
def get_sales(
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sale_type: Optional[str] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    cash_session_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    sales = get_sales_service(
        db=db,
        restaurant_id=restaurant_id,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        sale_type=sale_type,
        payment_method=payment_method,
        status=status,
        cash_session_id=cash_session_id
    )

    return [
        {
            "id": sale.id,
            "restaurant_id": sale.restaurant_id,
            "user_id": sale.user_id,
            "cash_session_id": sale.cash_session_id,
            "invoice_number": sale.invoice_number,

            "sale_type": sale.sale_type,
            "payment_method": sale.payment_method,
            "status": sale.status,

            "table_number": sale.table_number,
            "attendant_name": sale.attendant_name,

            "customer_name": sale.customer_name,
            "customer_phone": sale.customer_phone,
            "delivery_address": sale.delivery_address,
            "notes": sale.notes,

            "subtotal": float(sale.subtotal),
            "total": float(sale.total),
            "created_at": sale.created_at.isoformat(),

            "payments": [
                {
                    "payment_method": payment.payment_method,
                    "amount": float(payment.amount)
                }
                for payment in sale.payments
            ],

            "details": [
                {
                    "id": detail.id,
                    "product_id": detail.product_id,
                    "product_name": detail.product_name,
                    "quantity": detail.quantity,
                    "unit_price": float(detail.unit_price),
                    "line_total": float(detail.line_total)
                }
                for detail in sale.details
            ]
        }
        for sale in sales
    ]


# =========================
# CAMBIAR ESTADO
# =========================
@router.put("/{sale_id}/status")
def update_sale_status(
    sale_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    sale = update_sale_status_service(
        db=db,
        sale_id=sale_id,
        status=status,
        current_user=current_user
    )

    return {
        "message": "Estado actualizado correctamente",
        "sale_id": sale.id,
        "new_status": sale.status
    }


# =========================
# AGREGAR PRODUCTO A ORDEN
# =========================
@router.post("/{sale_id}/add-product")
def add_product_to_sale(
    sale_id: int,
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    sale = add_product_to_sale_service(
        db=db,
        sale_id=sale_id,
        product_id=product_id,
        quantity=quantity,
        current_user=current_user
    )

    total_paid = sum(payment.amount for payment in sale.payments)
    balance = sale.total - total_paid

    return {
        "message": "Producto agregado correctamente",
        "sale_id": sale.id,
        "subtotal": float(sale.subtotal),
        "total": float(sale.total),
        "paid": float(total_paid),
        "balance": float(balance),
        "details": [
            {
                "id": detail.id,
                "product_id": detail.product_id,
                "product_name": detail.product_name,
                "quantity": detail.quantity,
                "unit_price": float(detail.unit_price),
                "line_total": float(detail.line_total)
            }
            for detail in sale.details
        ]
    }


# =========================
# AGREGAR PAGOS A ORDEN
# =========================
@router.post("/{sale_id}/add-payment")
def add_payment_to_sale(
    sale_id: int,
    data: AddPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    sale = add_payment_to_sale_service(
        db=db,
        sale_id=sale_id,
        payments_data=data,
        current_user=current_user
    )

    total_paid = sum(payment.amount for payment in sale.payments)
    balance = sale.total - total_paid

    return {
        "message": "Pago registrado correctamente",
        "sale_id": sale.id,
        "total": float(sale.total),
        "paid": float(total_paid),
        "balance": float(balance)
    }


# =========================
# ANALÍTICA
# =========================
@router.get("/summary")
def sales_summary(
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return sales_summary_service(db, restaurant_id, current_user, start_date, end_date)


@router.get("/top-products")
def top_products(
    restaurant_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return top_products_service(db, restaurant_id, current_user, limit)


@router.get("/daily")
def daily_sales(
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return daily_sales_service(db, restaurant_id, current_user, start_date, end_date)


@router.get("/dashboard")
def dashboard(
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return dashboard_service(
        db,
        restaurant_id,
        current_user,
        start_date,
        end_date,
        limit
    )