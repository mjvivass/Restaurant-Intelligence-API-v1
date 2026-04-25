from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_model import User
from app.core.security import require_employee
from app.services.report_service import (
    get_sale_for_report,
    generate_sale_invoice_pdf
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/sales/{sale_id}/invoice")
def download_sale_invoice(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee)
):
    sale = get_sale_for_report(db, sale_id, current_user)
    pdf_buffer = generate_sale_invoice_pdf(sale)

    filename = f"factura_{sale.invoice_number}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )