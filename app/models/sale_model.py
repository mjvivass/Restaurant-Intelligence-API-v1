from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relaciones
    restaurant = relationship("Restaurant", back_populates="sales")
    product = relationship("Product", back_populates="sales")


# Índice compuesto para consultas por restaurante y fecha
Index("idx_sales_restaurant_date", Sale.restaurant_id, Sale.created_at)