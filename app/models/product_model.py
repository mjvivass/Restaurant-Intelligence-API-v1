from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(250), nullable=True)
    price = Column(Float, nullable=False)

    # INVENTARIO
    stock = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, nullable=False, default=5)
    last_updated = Column(DateTime, default=datetime.utcnow)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    # RELACIONES
    restaurant = relationship("Restaurant", back_populates="products")
    sales = relationship("Sale", back_populates="product")