from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.services.sales_analytics_service import sales_summary_service
from app.services.sale_service import create_sale_service
from app.db.session import get_db
from app.models.user_model import User
from app.schemas.sale_schema import SaleCreate, SaleResponse
from app.core.security import get_current_user
from sqlalchemy import desc
from app.models.product_model import Product
from app.services.sales_analytics_service import top_products_service
from app.services.sales_analytics_service import daily_sales_service
from app.services.sales_analytics_service import dashboard_service

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/", response_model=SaleResponse)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_sale_service(db, sale, current_user)

@router.get("/summary")
def sales_summary(
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return sales_summary_service(
        db,
        restaurant_id,
        current_user,
        start_date,
        end_date
    )
@router.get("/top-products")
def top_products(
    restaurant_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return top_products_service(
        db,
        restaurant_id,
        current_user,
        limit
    )
@router.get("/daily")
def daily_sales(
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return daily_sales_service(
        db,
        restaurant_id,
        current_user,
        start_date,
        end_date
    )
    return daily_sales_service(
        db,
        restaurant_id,
        current_user,
        start_date,
        end_date
    )

@router.get("/dashboard")
def dashboard(
    restaurant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return dashboard_service(
        db,
        restaurant_id,
        current_user,
        start_date,
        end_date,
        limit
    )
