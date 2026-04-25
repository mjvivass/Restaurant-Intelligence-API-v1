from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    address = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_restaurants"
    )

    users = relationship(
        "User",
        foreign_keys="User.restaurant_id",
        back_populates="restaurant"
    )

    products = relationship("Product", back_populates="restaurant")
    sales = relationship("Sale", back_populates="restaurant")
    cash_sessions = relationship("CashSession", back_populates="restaurant")