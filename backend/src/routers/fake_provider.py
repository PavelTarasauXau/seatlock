import httpx
from fastapi import APIRouter, Request

from src.routers.payments import sign_payload
from src.schemas import PaymentWebhook, WebhookStatus

# Dev-only stand-in for a payment provider: signs a webhook and sends it to our /payments/webhook
router = APIRouter(prefix="/fake-provider", tags=["Fake provider"])

@router.post("/payments/{provider_ref}/complete")
async def complete_payment(provider_ref: str, result: WebhookStatus, request: Request):
    body = PaymentWebhook(provider_ref=provider_ref, status=result).model_dump_json().encode()

    # ASGITransport calls our own app in-process, no real network needed
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=request.app),
        base_url="http://fake-provider",
    ) as client:
        response = await client.post(
            "/payments/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Signature": sign_payload(body)},
        )

    return {"webhook_status_code": response.status_code, "webhook_response": response.json()}
