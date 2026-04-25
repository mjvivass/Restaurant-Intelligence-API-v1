from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String, Text, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


# =========================
# CAJA
# =========================
class CashSession(Base):
    __tablename__ = "cash_sessions"

    id = Column(Integer, primary_key=True, index=True)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    opening_amount = Column(Float, nullable=False, default=0)
    closing_amount = Column(Float, nullable=True)

    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    status = Column(String(20), nullable=False, default="open")  # open / closed
    notes = Column(Text, nullable=True)

    restaurant = relationship("Restaurant", back_populates="cash_sessions")
    user = relationship("User", back_populates="cash_sessions")
    sales = relationship("Sale", back_populates="cash_session")


# =========================
# VENTA / ORDEN
# =========================
class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=False)

    invoice_number = Column(String(50), unique=True, nullable=False, index=True)

    sale_type = Column(String(20), nullable=False, default="onsite")  # onsite / delivery / pickup

    # compatibilidad con filtros actuales
    payment_method = Column(String(20), nullable=False, default="cash")

    # flujo de la orden
    status = Column(String(20), nullable=False, default="creada")
    # creada / confirmada / preparando / lista / entregada / cancelada

    # control de inventario
    stock_discounted = Column(Boolean, nullable=False, default=False)

    # extras tipo restaurante
    table_number = Column(String(10), nullable=True)
    attendant_name = Column(String(100), nullable=True)

    customer_name = Column(String(150), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    delivery_address = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    subtotal = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    restaurant = relationship("Restaurant", back_populates="sales")
    user = relationship("User", back_populates="sales")
    cash_session = relationship("CashSession", back_populates="sales")

    details = relationship(
        "SaleDetail",
        back_populates="sale",
        cascade="all, delete-orphan"
    )

    payments = relationship(
        "SalePayment",
        back_populates="sale",
        cascade="all, delete-orphan"
    )


# =========================
# DETALLE DE PRODUCTOS
# =========================
class SaleDetail(Base):
    __tablename__ = "sale_details"

    id = Column(Integer, primary_key=True, index=True)

    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    product_name = Column(String(150), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="details")
    product = relationship("Product", back_populates="sale_details")


# =========================
# PAGOS MÚLTIPLES
# =========================
class SalePayment(Base):
    __tablename__ = "sale_payments"

    id = Column(Integer, primary_key=True, index=True)

    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    payment_method = Column(String(20), nullable=False)  # cash / card / transfer / nequi / daviplata
    amount = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="payments")


# =========================
# ÍNDICES
# =========================
Index("idx_sales_restaurant_date", Sale.restaurant_id, Sale.created_at)
Index("idx_cash_sessions_restaurant_status", CashSession.restaurant_id, CashSession.status)