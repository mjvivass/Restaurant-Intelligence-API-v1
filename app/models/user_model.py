from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)

    restaurant = relationship(
        "Restaurant",
        foreign_keys=[restaurant_id],
        back_populates="users"
    )

    owned_restaurants = relationship(
        "Restaurant",
        foreign_keys="Restaurant.owner_id",
        back_populates="owner"
    )

    sales = relationship("Sale", back_populates="user")
    cash_sessions = relationship("CashSession", back_populates="user")