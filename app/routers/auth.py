from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import register_user, login_user
from app.core.security import get_current_user
from app.models.user_model import User

router = APIRouter(tags=["Auth"])


# =========================
# REGISTER
# =========================
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return register_user(user, db)


# =========================
# LOGIN
# =========================
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    return login_user(form_data, db)


# =========================
# CURRENT USER
# =========================
@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user