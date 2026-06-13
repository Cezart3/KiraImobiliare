"""Stripe one-time billing: a single 15 RON payment grants 30 days of access.

NOT a subscription — nothing auto-renews, so there is nothing to "cancel" and no
Billing Portal. When access expires the user simply buys another 30 days
(manual renewal). This keeps the consumer-law surface tiny (no recurring-charge
obligations) and matches the seasonal usage pattern.

Apple Pay / Google Pay appear automatically in Stripe Checkout once wallets are
enabled in the Stripe dashboard (plus domain verification in production).
"""
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.core import ratelimit
from app.core.config import settings
from app.db.models import User, utcnow

log = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

ACCESS_DAYS = 30


def _require_stripe() -> None:
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(
            status_code=503,
            detail="Plățile nu sunt configurate (RS_STRIPE_SECRET_KEY / RS_STRIPE_PRICE_ID)",
        )
    stripe.api_key = settings.stripe_secret_key


def grant_access(db: Session, user: User, days: int = ACCESS_DAYS) -> None:
    """Add `days` of access. If access is still active, extend from its end
    (stacking renewals); otherwise start from now."""
    active = user.sub_period_end and user.sub_period_end > utcnow()
    base = user.sub_period_end if active else utcnow()
    user.sub_period_end = base + timedelta(days=days)
    user.sub_status = "active"
    db.commit()
    log.info("billing: granted %dd to %s -> until %s", days, user.email, user.sub_period_end)


@router.post("/checkout")
def create_checkout(
    request: Request,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """One-time Checkout for 30 days of access. Buying again while still active
    stacks another 30 days (manual renewal)."""
    ratelimit.enforce(request, "billing", 10)
    _require_stripe()
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email)
        user.stripe_customer_id = customer["id"]
        db.commit()
    session = stripe.checkout.Session.create(
        mode="payment",  # one-time, NOT a subscription
        customer=user.stripe_customer_id,
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=f"{settings.app_base_url}/?plata=succes",
        cancel_url=f"{settings.app_base_url}/?plata=anulat",
        metadata={"user_id": str(user.id), "grants_days": str(ACCESS_DAYS)},
        # double-click guard: within a 10-min window Stripe replays the SAME
        # checkout session instead of opening a second one
        idempotency_key=f"checkout-{user.id}-{int(time.time() // 600)}",
    )
    return {"url": session["url"]}


@router.post("/sync")
def sync_payment(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Called by the frontend after the Checkout success redirect — makes local
    dev work without a webhook tunnel. Grants access for the most recent PAID
    one-time session not yet credited."""
    _require_stripe()
    if not user.stripe_customer_id:
        return {"subscribed": False}
    sessions = stripe.checkout.Session.list(customer=user.stripe_customer_id, limit=5)
    for s in sessions.get("data") or []:
        if s.get("payment_status") == "paid" and not _is_credited(db, user, s):
            grant_access(db, user)
            _mark_credited(user, s)
            db.commit()
            break
    db.refresh(user)
    return {"subscribed": user.has_access(), "sub_status": user.sub_status}


# We credit each paid Checkout session once. Track the last credited session id
# on the user so /sync and the webhook never double-grant for the same payment.
def _is_credited(db: Session, user: User, session: dict) -> bool:
    return user.last_payment_session == session.get("id")


def _mark_credited(user: User, session: dict) -> None:
    user.last_payment_session = session.get("id")


@router.post("/webhook")
async def webhook(request: Request, db: Annotated[Session, Depends(get_db)]):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from e

    if event["type"] == "checkout.session.completed":
        obj = event["data"]["object"]
        if obj.get("payment_status") == "paid":
            from sqlalchemy import select

            user = db.scalar(
                select(User).where(User.stripe_customer_id == obj.get("customer", ""))
            )
            if user is not None and not _is_credited(db, user, obj):
                grant_access(db, user)
                _mark_credited(user, obj)
                db.commit()
    return {"received": True}


# kept for type/import stability elsewhere; one-time model has no period concept
def _now_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
