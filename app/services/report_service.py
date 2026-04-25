from io import BytesIO
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.models.sale_model import Sale
from app.models.restaurant_model import Restaurant
from app.models.user_model import User


def get_sale_for_report(db: Session, sale_id: int, current_user: User):
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.details))
        .join(Restaurant, Sale.restaurant_id == Restaurant.id)
        .filter(
            Sale.id == sale_id,
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    return sale


def generate_sale_invoice_pdf(sale):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Restaurant IA")
    y -= 24

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, "Factura / Ticket de Venta")
    y -= 24

    pdf.drawString(50, y, f"Factura: {sale.invoice_number}")
    y -= 18
    pdf.drawString(50, y, f"Fecha: {sale.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 18
    pdf.drawString(50, y, f"Tipo de venta: {sale.sale_type}")
    y -= 18
    pdf.drawString(50, y, f"Metodo de pago: {sale.payment_method}")
    y -= 18
    pdf.drawString(50, y, f"Cliente: {sale.customer_name or 'Consumidor final'}")
    y -= 18

    if sale.customer_phone:
        pdf.drawString(50, y, f"Telefono: {sale.customer_phone}")
        y -= 18

    if sale.delivery_address:
        pdf.drawString(50, y, f"Direccion: {sale.delivery_address}")
        y -= 18

    if sale.notes:
        pdf.drawString(50, y, f"Notas: {sale.notes}")
        y -= 18

    y -= 8
    pdf.line(50, y, 550, y)
    y -= 20

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Producto")
    pdf.drawString(280, y, "Cant.")
    pdf.drawString(360, y, "Unit.")
    pdf.drawString(460, y, "Total")
    y -= 16

    pdf.setFont("Helvetica", 10)

    for detail in sale.details:
        if y < 80:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 10)

        pdf.drawString(50, y, str(detail.product_name))
        pdf.drawString(280, y, str(detail.quantity))
        pdf.drawString(360, y, f"${detail.unit_price:.2f}")
        pdf.drawString(460, y, f"${detail.line_total:.2f}")
        y -= 16

    y -= 8
    pdf.line(50, y, 550, y)
    y -= 20

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(350, y, "Subtotal:")
    pdf.drawString(460, y, f"${sale.subtotal:.2f}")
    y -= 18
    pdf.drawString(350, y, "Total:")
    pdf.drawString(460, y, f"${sale.total:.2f}")

    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, "Gracias por su compra.")

    pdf.save()
    buffer.seek(0)
    return buffer