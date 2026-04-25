from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


# =========================
# ITEMS DE LA VENTA
# =========================
class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int


# =========================
# PAGOS MÚLTIPLES
# =========================
class SalePaymentCreate(BaseModel):
    payment_method: str
    amount: float


class SalePaymentResponse(BaseModel):
    payment_method: str
    amount: float

    class Config:
        from_attributes = True


# =========================
# CREAR VENTA / ORDEN
# =========================
class SaleCreate(BaseModel):
    restaurant_id: int
    sale_type: str  # onsite / delivery / pickup

    # ahora puede venir vacío para permitir órdenes sin pago
    payments: List[SalePaymentCreate] = Field(default_factory=list)

    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None

    table_number: Optional[str] = None
    attendant_name: Optional[str] = None

    items: List[SaleItemCreate]


# =========================
# AGREGAR PAGOS A ORDEN EXISTENTE
# =========================
class AddPaymentRequest(BaseModel):
    payments: List[SalePaymentCreate]


# =========================
# RESPUESTA DETALLE
# =========================
class SaleDetailResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float

    class Config:
        from_attributes = True


# =========================
# RESPUESTA VENTA
# =========================
class SaleResponse(BaseModel):
    id: int
    restaurant_id: int
    user_id: int
    cash_session_id: int

    invoice_number: str
    sale_type: str
    payment_method: str
    status: str

    table_number: Optional[str] = None
    attendant_name: Optional[str] = None

    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None

    subtotal: float
    total: float
    created_at: datetime

    payments: List[SalePaymentResponse] = Field(default_factory=list)
    details: List[SaleDetailResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# =========================
# CAJA
# =========================
class CashOpenCreate(BaseModel):
    restaurant_id: int
    opening_amount: float
    notes: Optional[str] = None


class CashCloseCreate(BaseModel):
    closing_amount: float
    notes: Optional[str] = None


class CashSessionResponse(BaseModel):
    id: int
    restaurant_id: int
    user_id: int
    opening_amount: float
    closing_amount: Optional[float] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True