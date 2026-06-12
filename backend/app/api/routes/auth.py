"""Email + password auth and Google Sign-In, with a JWT session cookie.

Security notes:
- Session lives in an httpOnly, SameSite=Lax cookie — JS can't read it, and
  cross-site POSTs don't carry it (CSRF mitigation for the state-changing routes).
- Google login verifies the ID token signature + audience server-side via
  google-auth; we never trust the client's claims directly.
- All entry points are rate-limited per IP (in-memory sliding window).
"""
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core import ratelimit
from app.core.config import settings
from app.core.security import (
    COOKIE_NAME,
    create_session_token,
    hash_password,
    verify_password,
)
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Credentials(BaseModel):
    email: str
    password: str


class GoogleCredential(BaseModel):
    credential: str  # ID token (JWT) issued by Google Identity Services


class MeOut(BaseModel):
    authenticated: bool
    email: str | None = None
    subscribed: bool = False
    sub_status: str | None = None
    paywall_enabled: bool = True
    free_listing_limit: int = 0
    google_client_id: str | None = None  # frontend needs it to render the button


def _normalize_email(email: str) -> str:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Adresă de email invalidă")
    return email


def _set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(user_id),
        max_age=settings.session_days * 86400,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )


def _me(user: User | None) -> MeOut:
    return MeOut(
        authenticated=user is not None,
        email=user.email if user else None,
        subscribed=bool(user and user.has_access()),
        sub_status=user.sub_status if user else None,
        paywall_enabled=settings.paywall_enabled,
        free_listing_limit=settings.free_listing_limit,
        google_client_id=settings.google_client_id or None,
    )


def _verify_google_token(credential: str) -> dict:
    """Returns the verified ID-token claims. Separate function so tests can stub it."""
    return google_id_token.verify_oauth2_token(
        credential, google_requests.Request(), settings.google_client_id
    )


@router.post("/register", response_model=MeOut)
def register(
    creds: Credentials,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    ratelimit.enforce(request, "auth", settings.auth_rate_limit_per_min)
    email = _normalize_email(creds.email)
    if len(creds.password) < 8:
        raise HTTPException(status_code=422, detail="Parola: minim 8 caractere")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Există deja un cont cu acest email")
    user = User(email=email, password_hash=hash_password(creds.password))
    db.add(user)
    db.commit()
    _set_session(response, user.id)
    return _me(user)


@router.post("/login", response_model=MeOut)
def login(
    creds: Credentials,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    ratelimit.enforce(request, "auth", settings.auth_rate_limit_per_min)
    email = _normalize_email(creds.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is not None and not user.password_hash:
        raise HTTPException(
            status_code=401,
            detail="Cont creat cu Google — folosește butonul „Continuă cu Google”",
        )
    if user is None or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email sau parolă greșite")
    _set_session(response, user.id)
    return _me(user)


@router.post("/google", response_model=MeOut)
def google_login(
    body: GoogleCredential,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    ratelimit.enforce(request, "auth", settings.auth_rate_limit_per_min)
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503, detail="Autentificarea Google nu este configurată"
        )
    try:
        claims = _verify_google_token(body.credential)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Token Google invalid") from e
    email = (claims.get("email") or "").strip().lower()
    if not email or not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="Email Google neverificat")
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        # Google-only account: empty password hash; password login is rejected
        # explicitly in /login (verify_password also fails safe on empty hashes).
        user = User(email=email, password_hash="")
        db.add(user)
        db.commit()
    _set_session(response, user.id)
    return _me(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.post("/delete-account")
def delete_account(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user)] = None,
):
    """GDPR right to erasure: cancel any live Stripe subscription, then delete
    the account row. Irreversible."""
    ratelimit.enforce(request, "auth", settings.auth_rate_limit_per_min)
    if user is None:
        raise HTTPException(status_code=401, detail="Autentificare necesară")
    if user.stripe_customer_id and settings.stripe_secret_key:
        import stripe

        stripe.api_key = settings.stripe_secret_key
        try:
            subs = stripe.Subscription.list(
                customer=user.stripe_customer_id, status="all", limit=10
            )
            for s in subs.get("data") or []:
                if s.get("status") in ("active", "trialing", "past_due"):
                    stripe.Subscription.cancel(s["id"])
        except stripe.error.StripeError:
            raise HTTPException(
                status_code=502,
                detail="Nu am putut anula abonamentul Stripe. Reîncearcă sau "
                "anulează întâi din „Gestionează abonamentul”.",
            ) from None
    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=MeOut)
def me(user: Annotated[User | None, Depends(get_current_user)]):
    return _me(user)
