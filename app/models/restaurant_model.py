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
    address = Column(String(255))   # 👈 AGREGA ESTA LÍNEA
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relaciones
    products = relationship("Product", back_populates="restaurant")
    sales = relationship("Sale", back_populates="restaurant")
