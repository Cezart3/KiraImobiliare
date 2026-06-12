"""Stripe subscription billing: Checkout (subscribe), Billing Portal (cancel —
must stay as easy as subscribing), webhook + sync fallback for local dev.

Apple Pay / Google Pay appear automatically in Stripe Checkout once wallets are
enabled in the Stripe dashboard (plus domain verification in production).
"""
import logging
import time
from datetime import UTC, datetime
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.core import ratelimit
from app.core.config import settings
from app.db.models import User

log = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

# Stripe subscription status -> our sub_status
_STATUS_MAP = {
    "active": "active",
    "trialing": "active",
    "past_due": "past_due",
    "canceled": "canceled",
    "unpaid": "canceled",
    "incomplete": "none",
    "incomplete_expired": "none",
    "paused": "canceled",
}


def _require_stripe() -> None:
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(
            status_code=503,
            detail="Plățile nu sunt configurate (RS_STRIPE_SECRET_KEY / RS_STRIPE_PRICE_ID)",
        )
    stripe.api_key = settings.stripe_secret_key


def _period_end_ts(sub: dict) -> int | None:
    """current_period_end lives on the subscription (old API) or on its first
    item (2025+ API versions) — accept both."""
    ts = sub.get("current_period_end")
    if ts:
        return ts
    items = (sub.get("items") or {}).get("data") or []
    if items:
        return items[0].get("current_period_end")
    return None


def apply_subscription_state(db: Session, customer_id: str, sub: dict) -> User | None:
    """Shared by webhook + sync. Returns the updated user (or None)."""
    user = db.scalar(select(User).where(User.stripe_customer_id == customer_id))
    if user is None:
        log.warning("billing: no user for stripe customer %s", customer_id)
        return None
    user.sub_status = _STATUS_MAP.get(sub.get("status", ""), "none")
    ts = _period_end_ts(sub)
    user.sub_period_end = (
        datetime.fromtimestamp(ts, tz=UTC).replace(tzinfo=None) if ts else None
    )
    db.commit()
    log.info(
        "billing: %s -> %s until %s", user.email, user.sub_status, user.sub_period_end
    )
    return user


@router.post("/checkout")
def create_checkout(
    request: Request,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    ratelimit.enforce(request, "billing", 10)
    _require_stripe()
    if user.has_access():
        raise HTTPException(status_code=409, detail="Ai deja un abonament activ")
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email)
        user.stripe_customer_id = customer["id"]
        db.commit()
    else:
        # double-payment guard: if Stripe already has a live subscription for this
        # customer (e.g. webhook not delivered yet, second tab), sync + refuse
        subs = stripe.Subscription.list(
            customer=user.stripe_customer_id, status="all", limit=5
        )
        for s in subs.get("data") or []:
            if s.get("status") in ("active", "trialing", "past_due"):
                apply_subscription_state(db, user.stripe_customer_id, s)
                raise HTTPException(status_code=409, detail="Ai deja un abonament activ")
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=user.stripe_customer_id,
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=f"{settings.app_base_url}/?abonament=succes",
        cancel_url=f"{settings.app_base_url}/?abonament=anulat",
        # double-click guard: within a 10-min window Stripe replays the SAME
        # checkout session instead of opening a second one
        idempotency_key=f"checkout-{user.id}-{int(time.time() // 600)}",
    )
    return {"url": session["url"]}


@router.post("/portal")
def create_portal(
    user: Annotated[User, Depends(require_user)],
):
    _require_stripe()
    if not user.stripe_customer_id:
        raise HTTPException(status_code=409, detail="Nu există un abonament de gestionat")
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=settings.app_base_url,
    )
    return {"url": session["url"]}


@router.post("/sync")
def sync_subscription(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Called by the frontend after the Checkout success redirect — makes local
    dev work without a webhook tunnel."""
    _require_stripe()
    if not user.stripe_customer_id:
        return {"subscribed": False}
    subs = stripe.Subscription.list(
        customer=user.stripe_customer_id, status="all", limit=5
    )
    data = subs.get("data") or []
    if data:
        best = next((s for s in data if s.get("status") == "active"), data[0])
        apply_subscription_state(db, user.stripe_customer_id, best)
        db.refresh(user)
    return {"subscribed": user.has_access(), "sub_status": user.sub_status}


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

    etype = event["type"]
    obj = event["data"]["object"]
    if etype in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        apply_subscription_state(db, obj.get("customer", ""), obj)
    elif etype == "checkout.session.completed" and obj.get("subscription"):
        stripe.api_key = settings.stripe_secret_key
        sub = stripe.Subscription.retrieve(obj["subscription"])
        apply_subscription_state(db, obj.get("customer", ""), sub)
    return {"received": True}
