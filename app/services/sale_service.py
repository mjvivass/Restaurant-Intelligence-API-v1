from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from datetime import datetime
import uuid

from app.models.product_model import Product
from app.models.sale_model import Sale, SaleDetail, CashSession, SalePayment
from app.models.restaurant_model import Restaurant
from app.models.user_model import User
from app.schemas.sale_schema import (
    SaleCreate,
    CashOpenCreate,
    CashCloseCreate,
    AddPaymentRequest,
)


# =========================
# HELPERS
# =========================
def _get_owned_restaurant(db: Session, restaurant_id: int, current_user: User):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=403, detail="No autorizado")

    return restaurant


def _generate_invoice_number(restaurant_id: int) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8].upper()
    return f"FAC-{restaurant_id}-{timestamp}-{random_part}"


def _recalculate_sale_totals(sale: Sale):
    subtotal = sum(detail.line_total for detail in sale.details)
    sale.subtotal = subtotal
    sale.total = subtotal
    return subtotal


def _get_sale_total_paid(sale: Sale) -> float:
    return float(sum(payment.amount for payment in sale.payments))


def _validate_sale_stock_available(db: Session, sale: Sale):
    for detail in sale.details:
        product = db.query(Product).filter(
            Product.id == detail.product_id,
            Product.restaurant_id == sale.restaurant_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Producto asociado no encontrado: {detail.product_name}"
            )

        if product.stock < detail.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {product.name}"
            )


def _discount_stock_for_sale(db: Session, sale: Sale):
    if sale.stock_discounted:
        return

    for detail in sale.details:
        product = db.query(Product).filter(
            Product.id == detail.product_id,
            Product.restaurant_id == sale.restaurant_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Producto asociado no encontrado: {detail.product_name}"
            )

        if product.stock < detail.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {product.name}"
            )

        product.stock -= detail.quantity
        product.last_updated = datetime.utcnow()

    sale.stock_discounted = True


def _restore_stock_for_sale(db: Session, sale: Sale):
    if not sale.stock_discounted:
        return

    for detail in sale.details:
        product = db.query(Product).filter(
            Product.id == detail.product_id,
            Product.restaurant_id == sale.restaurant_id
        ).first()

        if not product:
            continue

        product.stock += detail.quantity
        product.last_updated = datetime.utcnow()

    sale.stock_discounted = False


# =========================
# CAJA
# =========================
def open_cash_session_service(
    db: Session,
    cash_data: CashOpenCreate,
    current_user: User
):
    _get_owned_restaurant(db, cash_data.restaurant_id, current_user)

    existing_open = db.query(CashSession).filter(
        CashSession.restaurant_id == cash_data.restaurant_id,
        CashSession.status == "open"
    ).first()

    if existing_open:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una caja abierta para este restaurante"
        )

    new_session = CashSession(
        restaurant_id=cash_data.restaurant_id,
        user_id=current_user.id,
        opening_amount=cash_data.opening_amount,
        notes=cash_data.notes,
        status="open"
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


def get_current_cash_session_service(
    db: Session,
    restaurant_id: int,
    current_user: User
):
    _get_owned_restaurant(db, restaurant_id, current_user)

    cash_session = db.query(CashSession).filter(
        CashSession.restaurant_id == restaurant_id,
        CashSession.status == "open"
    ).first()

    if not cash_session:
        raise HTTPException(status_code=404, detail="No hay caja abierta")

    return cash_session


def close_cash_session_service(
    db: Session,
    cash_session_id: int,
    close_data: CashCloseCreate,
    current_user: User
):
    cash_session = (
        db.query(CashSession)
        .join(Restaurant, CashSession.restaurant_id == Restaurant.id)
        .filter(
            CashSession.id == cash_session_id,
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not cash_session:
        raise HTTPException(status_code=404, detail="Caja no encontrada")

    if cash_session.status != "open":
        raise HTTPException(status_code=400, detail="La caja ya está cerrada")

    sales = (
        db.query(Sale)
        .options(joinedload(Sale.payments))
        .filter(
            Sale.cash_session_id == cash_session.id,
            Sale.status != "cancelada"
        )
        .all()
    )

    total_sales_count = len(sales)

    payment_summary = {}
    total_payments_received = 0.0

    for sale in sales:
        if sale.payments:
            for payment in sale.payments:
                payment_summary[payment.payment_method] = (
                    payment_summary.get(payment.payment_method, 0) + payment.amount
                )
                total_payments_received += payment.amount

    expected_amount = cash_session.opening_amount + total_payments_received
    difference = close_data.closing_amount - expected_amount

    cash_session.closing_amount = close_data.closing_amount
    cash_session.closed_at = datetime.utcnow()
    cash_session.status = "closed"
    cash_session.notes = close_data.notes or cash_session.notes

    db.commit()
    db.refresh(cash_session)

    return {
        "cash_session_id": cash_session.id,
        "restaurant_id": cash_session.restaurant_id,
        "opened_at": cash_session.opened_at,
        "closed_at": cash_session.closed_at,
        "opening_amount": cash_session.opening_amount,
        "closing_amount": cash_session.closing_amount,
        "expected_amount": expected_amount,
        "difference": difference,
        "total_sales_count": total_sales_count,
        "total_sales_amount": total_payments_received,
        "payment_summary": payment_summary
    }


# =========================
# CREAR VENTA / ORDEN
# =========================
def create_sale_service(
    db: Session,
    sale_data: SaleCreate,
    current_user: User
) -> Sale:
    _get_owned_restaurant(db, sale_data.restaurant_id, current_user)

    cash_session = db.query(CashSession).filter(
        CashSession.restaurant_id == sale_data.restaurant_id,
        CashSession.status == "open"
    ).first()

    if not cash_session:
        raise HTTPException(
            status_code=400,
            detail="Debes abrir una caja antes de registrar ventas"
        )

    if not sale_data.items or len(sale_data.items) == 0:
        raise HTTPException(
            status_code=400,
            detail="La venta debe tener al menos un producto"
        )

    subtotal = 0
    detail_rows = []

    for item in sale_data.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.restaurant_id == sale_data.restaurant_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Producto {item.product_id} no encontrado"
            )

        if item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="La cantidad debe ser mayor a 0"
            )

        # en creada solo validamos disponibilidad actual, no descontamos todavía
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {product.name}"
            )

        line_total = product.price * item.quantity
        subtotal += line_total

        detail_rows.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit_price": product.price,
            "line_total": line_total
        })

    total = subtotal

    if sale_data.sale_type == "delivery" and not sale_data.delivery_address:
        raise HTTPException(
            status_code=400,
            detail="La dirección es obligatoria para pedidos a domicilio"
        )

    if sale_data.payments:
        total_payments = sum(payment.amount for payment in sale_data.payments)

        if total_payments > total + 0.01:
            raise HTTPException(
                status_code=400,
                detail="El total de pagos no puede exceder el total de la venta"
            )

    new_sale = Sale(
        restaurant_id=sale_data.restaurant_id,
        user_id=current_user.id,
        cash_session_id=cash_session.id,
        invoice_number=_generate_invoice_number(sale_data.restaurant_id),
        sale_type=sale_data.sale_type,
        payment_method=sale_data.payments[0].payment_method if sale_data.payments else "pending",
        status="creada",
        stock_discounted=False,
        table_number=sale_data.table_number,
        attendant_name=sale_data.attendant_name,
        customer_name=sale_data.customer_name,
        customer_phone=sale_data.customer_phone,
        delivery_address=sale_data.delivery_address,
        notes=sale_data.notes,
        subtotal=subtotal,
        total=total
    )

    db.add(new_sale)
    db.flush()

    for row in detail_rows:
        detail = SaleDetail(
            sale_id=new_sale.id,
            product_id=row["product_id"],
            product_name=row["product_name"],
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            line_total=row["line_total"]
        )
        db.add(detail)

    if sale_data.payments:
        for payment in sale_data.payments:
            if payment.amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Los montos de pago deben ser mayores a 0"
                )

            db.add(SalePayment(
                sale_id=new_sale.id,
                payment_method=payment.payment_method,
                amount=payment.amount
            ))

    db.commit()

    sale = (
        db.query(Sale)
        .options(
            joinedload(Sale.details),
            joinedload(Sale.payments)
        )
        .filter(Sale.id == new_sale.id)
        .first()
    )

    return sale


# =========================
# LISTAR VENTAS
# =========================
def get_sales_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
    start_date=None,
    end_date=None,
    sale_type=None,
    payment_method=None,
    status=None,
    cash_session_id=None
):
    _get_owned_restaurant(db, restaurant_id, current_user)

    query = (
        db.query(Sale)
        .options(
            joinedload(Sale.details),
            joinedload(Sale.payments)
        )
        .filter(Sale.restaurant_id == restaurant_id)
        .order_by(Sale.created_at.desc())
    )

    if start_date:
        query = query.filter(Sale.created_at >= start_date)

    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    if sale_type:
        query = query.filter(Sale.sale_type == sale_type)

    if payment_method:
        query = query.join(SalePayment).filter(
            SalePayment.payment_method == payment_method
        )

    if status:
        query = query.filter(Sale.status == status)

    if cash_session_id:
        query = query.filter(Sale.cash_session_id == cash_session_id)

    return query.all()


# =========================
# CAMBIAR ESTADO DE ORDEN
# =========================
def update_sale_status_service(
    db: Session,
    sale_id: int,
    status: str,
    current_user: User
):
    valid_statuses = [
        "creada",
        "confirmada",
        "preparando",
        "lista",
        "entregada",
        "cancelada"
    ]

    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Estado inválido")

    sale = (
        db.query(Sale)
        .options(joinedload(Sale.details), joinedload(Sale.payments))
        .join(Restaurant, Sale.restaurant_id == Restaurant.id)
        .filter(
            Sale.id == sale_id,
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    current_status = sale.status

    valid_transitions = {
        "creada": ["confirmada", "cancelada"],
        "confirmada": ["preparando", "cancelada"],
        "preparando": ["lista"],
        "lista": ["entregada"],
        "entregada": [],
        "cancelada": [],
    }

    if status != current_status and status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede pasar de {current_status} a {status}"
        )

    if current_status == status:
        return sale

    if status == "confirmada":
        _validate_sale_stock_available(db, sale)
        _discount_stock_for_sale(db, sale)

    if status == "cancelada":
        if current_status in ["confirmada", "preparando", "lista"] and sale.stock_discounted:
            _restore_stock_for_sale(db, sale)

    sale.status = status

    db.commit()
    db.refresh(sale)

    return sale


# =========================
# AGREGAR PRODUCTO A ORDEN EXISTENTE
# =========================
def add_product_to_sale_service(
    db: Session,
    sale_id: int,
    product_id: int,
    quantity: int,
    current_user: User
):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")

    sale = (
        db.query(Sale)
        .options(
            joinedload(Sale.details),
            joinedload(Sale.payments)
        )
        .join(Restaurant, Sale.restaurant_id == Restaurant.id)
        .filter(
            Sale.id == sale_id,
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if sale.status in ["preparando", "lista", "entregada", "cancelada"]:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden agregar productos en órdenes creadas o confirmadas"
        )

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.restaurant_id == sale.restaurant_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if product.stock < quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    line_total = product.price * quantity

    existing_detail = next(
        (detail for detail in sale.details if detail.product_id == product_id),
        None
    )

    if existing_detail:
        existing_detail.quantity += quantity
        existing_detail.line_total = existing_detail.quantity * existing_detail.unit_price
    else:
        db.add(SaleDetail(
            sale_id=sale.id,
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price,
            line_total=line_total
        ))

    # si la orden ya estaba confirmada y el stock ya fue descontado,
    # este nuevo producto sí debe descontarse de inmediato
    if sale.status == "confirmada" and sale.stock_discounted:
        if product.stock < quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente")
        product.stock -= quantity
        product.last_updated = datetime.utcnow()

    db.flush()

    sale = (
        db.query(Sale)
        .options(
            joinedload(Sale.details),
            joinedload(Sale.payments)
        )
        .filter(Sale.id == sale.id)
        .first()
    )

    _recalculate_sale_totals(sale)

    db.commit()
    db.refresh(sale)

    return sale


# =========================
# AGREGAR PAGOS A ORDEN
# =========================
def add_payment_to_sale_service(
    db: Session,
    sale_id: int,
    payments_data: AddPaymentRequest,
    current_user: User
):
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.payments))
        .join(Restaurant, Sale.restaurant_id == Restaurant.id)
        .filter(
            Sale.id == sale_id,
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if sale.status in ["entregada", "cancelada"]:
        raise HTTPException(
            status_code=400,
            detail="No se puede agregar pagos a una orden finalizada"
        )

    if not payments_data.payments or len(payments_data.payments) == 0:
        raise HTTPException(
            status_code=400,
            detail="Debes enviar al menos un pago"
        )

    total_paid = _get_sale_total_paid(sale)

    for payment in payments_data.payments:
        if payment.amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Los montos deben ser mayores a 0"
            )

        total_paid += payment.amount

        if total_paid > sale.total + 0.01:
            raise HTTPException(
                status_code=400,
                detail="El pago excede el total de la orden"
            )

        db.add(SalePayment(
            sale_id=sale.id,
            payment_method=payment.payment_method,
            amount=payment.amount
        ))

    if sale.payment_method == "pending" and payments_data.payments:
        sale.payment_method = payments_data.payments[0].payment_method

    db.commit()

    updated_sale = (
        db.query(Sale)
        .options(joinedload(Sale.payments))
        .filter(Sale.id == sale.id)
        .first()
    )

    return updated_sale