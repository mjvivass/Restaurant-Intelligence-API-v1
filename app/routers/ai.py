from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_model import User
from app.core.security import require_employee

from app.services.ai_service import (
    smart_alerts_service,
    smart_insights_service,
    sales_prediction_service
)

router = APIRouter(prefix="/ai", tags=["AI"])


# =========================
# ALERTAS
# =========================
@router.get("/alerts")
def get_alerts(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return smart_alerts_service(db, restaurant_id, current_user)


# =========================
# INSIGHTS
# =========================
@router.get("/insights")
def get_insights(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return smart_insights_service(db, restaurant_id, current_user)


# =========================
# PREDICCIÓN
# =========================
@router.get("/prediction")
def get_prediction(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    return sales_prediction_service(db, restaurant_id, current_user)