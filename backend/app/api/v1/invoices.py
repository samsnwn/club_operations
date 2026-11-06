"""Public invoice facade; the invoice service remains the implementation."""

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.core.config import get_settings

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _service_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_settings().invoice_service_token}"}


async def _request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    raw_response: bool = False,
) -> Any:
    settings = get_settings()
    url = f"{settings.invoice_service_url.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, url, headers=_service_headers(), json=json, params=params
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, detail="Invoice service unavailable"
        ) from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    if raw_response:
        return response
    return response.json()


@router.post("/import")
async def import_invoices() -> dict:
    return await _request("POST", "/api/v1/internal/invoices/import")


@router.get("/queue")
async def invoice_queue(status: str = "all") -> Any:
    if status == "all":
        pending = await _request(
            "GET", "/api/v1/queue", params={"status": "pending_review"}
        )
        attention = await _request(
            "GET", "/api/v1/queue", params={"status": "needs_attention"}
        )
        items = [*pending["items"], *attention["items"]]
        items.sort(key=lambda item: (item["confidence"], item["created_at"]))
        return {"count": len(items), "items": items}
    return await _request("GET", "/api/v1/queue", params={"status": status})


@router.get("/{invoice_id}")
async def invoice_detail(invoice_id: int) -> Any:
    return await _request("GET", f"/api/v1/queue/{invoice_id}")


@router.get("/{invoice_id}/original")
async def invoice_original(invoice_id: int) -> Response:
    response = await _request(
        "GET",
        f"/api/v1/internal/invoices/{invoice_id}/original",
        raw_response=True,
    )
    return Response(
        content=response.content,
        media_type=response.headers.get("content-type"),
        headers={"Content-Disposition": "inline"},
    )


@router.post("/{invoice_id}/confirm")
async def confirm_invoice(invoice_id: int, payload: dict[str, Any]) -> Any:
    return await _request("POST", f"/api/v1/queue/{invoice_id}/confirm", json=payload)


@router.post("/{invoice_id}/reject")
async def reject_invoice(invoice_id: int) -> Any:
    return await _request("POST", f"/api/v1/queue/{invoice_id}/reject")
