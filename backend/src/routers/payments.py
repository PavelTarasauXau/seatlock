import hashlib
import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, Request, Header, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select

from src.config import settings
from src.database import Session
from src.models import Booking, BookingStatus, Payment, PaymentStatus
from src.schemas import PaymentWebhook, WebhookStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])

def sign_payload(body: bytes) -> str:
    secret = settings.payment_webhook_secret.get_secret_value().encode()
    return hmac.new(secret, body, hashlib.sha256).hexdigest()

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    session: Session,
    x_signature: Annotated[str, Header()],
):
    # The signature is computed over the raw bytes, so check it before parsing JSON
    body = await request.body()
    if not hmac.compare_digest(sign_payload(body), x_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    try:
        payload = PaymentWebhook.model_validate_json(body)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors(),
        )

    payment = await session.scalar(
        select(Payment).where(Payment.provider_ref == payload.provider_ref)
    )
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    # Lock booking first, then payment: same order as /pay and cancel
    booking = await session.get(Booking, payment.booking_id, with_for_update=True)
    await session.refresh(payment, with_for_update=True)

    # Repeated webhook: already processed, answer 200 so the provider stops retrying
    if payment.status != PaymentStatus.PENDING:
        return {"ok": True}

    if payload.status == WebhookStatus.SUCCEEDED:
        payment.status = PaymentStatus.SUCCEEDED
        if booking.status == BookingStatus.PENDING_PAYMENT:
            booking.status = BookingStatus.PAID
        elif booking.status == BookingStatus.CANCELLED:
            # Money was taken for a cancelled booking; a real provider refund call would go here
            booking.status = BookingStatus.REFUNDED
            logger.warning("Payment %s succeeded for cancelled booking %s, refunded", payment.id, booking.id)
    else:
        # Booking stays pending_payment, so the user can retry with a new idempotency key
        payment.status = PaymentStatus.FAILED

    await session.commit()
    return {"ok": True}
