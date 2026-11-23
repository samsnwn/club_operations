"""Public invoice facade; the invoice service remains the implementation.

Every request is made on behalf of a signed-in user: the facade forwards the
internal service token **and** the caller's username, which the invoice service
uses to attribute confirm/reject actions. The username is taken from the
authenticated session, never from an inbound header.
"""

import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.auth.dependencies import require_role
from app.core.config import get_settings
from app.models import User

router = APIRouter(prefix="/invoices", tags=["invoices"])
log = logging.getLogger(__name__)

# Invoice review is an owner/admin capability. Staff accounts can sign in and
# manage their own password, but have no access to invoice data.
InvoiceReviewer = Annotated[User, Depends(require_role("owner", "admin"))]


def _service_headers(reviewer: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {get_settings().invoice_service_token}",
        "X-Reviewer": reviewer,
    }


# An import runs extraction synchronously in the invoice service and OCR may
# take up to two minutes per scanned file, so it gets its own budget.
IMPORT_TIMEOUT_SECONDS = 900.0


def _upstream_detail(response: httpx.Response) -> Any:
    """The service's own `detail`, so the UI shows its message, not raw JSON."""
    try:
        body = response.json()
    except ValueError:
        return response.text
    if isinstance(body, dict) and "detail" in body:
        return body["detail"]
    return response.text


def _client() -> httpx.AsyncClient:
    """HTTP client factory for invoice-service calls (test seam)."""
    return httpx.AsyncClient(timeout=30.0)


async def _request(
    method: str,
    path: str,
    *,
    reviewer: str,
    json: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    raw_response: bool = False,
    timeout: float | None = None,
) -> Any:
    settings = get_settings()
    url = f"{settings.invoice_service_url.rstrip('/')}{path}"
    extra: dict[str, Any] = {} if timeout is None else {"timeout": timeout}
    try:
        async with _client() as client:
            response = await client.request(
                method,
                url,
                headers=_service_headers(reviewer),
                json=json,
                params=params,
                **extra,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, detail="Invoice service unavailable"
        ) from exc
    if response.status_code in (401, 403):
        # The service refused the facade's own credentials (token mismatch).
        # That is a deployment fault, not the signed-in user's session, so it
        # must not reach the browser as an authentication error.
        log.error(
            "Invoice service rejected the internal token (%s) for %s %s",
            response.status_code,
            method,
            path,
        )
        raise HTTPException(
            status_code=502,
            detail="Invoice service rejected the platform's credentials",
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code, detail=_upstream_detail(response)
        )
    if raw_response:
        return response
    return response.json()


@router.post("/import")
async def import_invoices(user: InvoiceReviewer) -> dict:
    return await _request(
        "POST",
        "/api/v1/internal/invoices/import",
        reviewer=user.username,
        timeout=IMPORT_TIMEOUT_SECONDS,
    )


@router.get("/queue")
async def invoice_queue(user: InvoiceReviewer, status: str = "open") -> Any:
    """Open invoices by default; the service owns the order."""
    return await _request(
        "GET",
        "/api/v1/queue",
        reviewer=user.username,
        params={"status": status},
    )


@router.get("/{invoice_id}")
async def invoice_detail(invoice_id: int, user: InvoiceReviewer) -> Any:
    return await _request("GET", f"/api/v1/queue/{invoice_id}", reviewer=user.username)


@router.get("/{invoice_id}/original")
async def invoice_original(invoice_id: int, user: InvoiceReviewer) -> Response:
    response = await _request(
        "GET",
        f"/api/v1/internal/invoices/{invoice_id}/original",
        reviewer=user.username,
        raw_response=True,
    )
    return Response(
        content=response.content,
        media_type=response.headers.get("content-type"),
        headers={"Content-Disposition": "inline"},
    )


@router.post("/{invoice_id}/confirm")
async def confirm_invoice(
    invoice_id: int,
    payload: dict[str, Any],
    user: InvoiceReviewer,
) -> Any:
    return await _request(
        "POST",
        f"/api/v1/queue/{invoice_id}/confirm",
        reviewer=user.username,
        json=payload,
    )


@router.post("/{invoice_id}/reject")
async def reject_invoice(invoice_id: int, user: InvoiceReviewer) -> Any:
    return await _request(
        "POST", f"/api/v1/queue/{invoice_id}/reject", reviewer=user.username
    )
