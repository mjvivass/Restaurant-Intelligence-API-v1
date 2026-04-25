from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user_model import User
from app.core.security import hash_password, verify_password, create_access_token
from datetime import timedelta


def register_user(user_data, db: Session):
    existing_user = db.query(User).filter(
        (User.email == user_data.email) |
        (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")

    hashed = hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed,
        role="admin"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(form_data, db: Session):
    user = db.query(User).filter(
        (User.email == form_data.username) |
        (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(
        data={
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=timedelta(minutes=30)
    )

    refresh_token = create_access_token(
        data={
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=timedelta(days=7)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }