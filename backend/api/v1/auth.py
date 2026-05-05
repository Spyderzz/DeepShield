from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.deps import get_current_user
from config import settings
from db.database import get_db
from db.models import User
from schemas.auth import LoginBody, RegisterBody, TokenResponse, UserOut
from services.auth_service import authenticate, create_access_token, register_user, hash_password
from services.rate_limit import ANON_AUTH_LOGIN, ANON_AUTH_REGISTER, limiter

router = APIRouter(prefix="/auth", tags=["auth"])

_OAUTH_TTL_SECONDS = 10 * 60


def _normalize_redirect_path(value: str | None) -> str:
    redirect_to = (value or "/analyze").strip()
    if not redirect_to.startswith("/") or redirect_to.startswith("//"):
        return "/analyze"
    return redirect_to


def _provider_config(provider: str) -> dict[str, str]:
    provider = provider.lower().strip()
    if provider == "google":
        return {
            "client_id": settings.GOOGLE_CLIENT_ID.strip(),
            "client_secret": settings.GOOGLE_CLIENT_SECRET.strip(),
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile",
        }
    if provider == "github":
        return {
            "client_id": settings.GITHUB_CLIENT_ID.strip(),
            "client_secret": settings.GITHUB_CLIENT_SECRET.strip(),
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "emails_url": "https://api.github.com/user/emails",
            "scope": "read:user user:email",
        }
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Unsupported OAuth provider")


def _state_sign(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") + "." + sig


def _state_verify(state: str) -> dict[str, object] | None:
    try:
        raw_b64, sig = state.split(".", 1)
        padded = raw_b64 + "=" * (-len(raw_b64) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        expected = hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return None
        payload = json.loads(raw.decode("utf-8"))
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


async def _fetch_google_profile(code: str, redirect_uri: str) -> dict[str, str]:
    cfg = _provider_config("google")
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_res = await client.post(cfg["token_url"], data={
            "code": code,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, headers={"Accept": "application/json"})
        token_res.raise_for_status()
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google OAuth token exchange failed")
        user_res = await client.get(cfg["userinfo_url"], headers={"Authorization": f"Bearer {access_token}"})
        user_res.raise_for_status()
        profile = user_res.json()
        email = (profile.get("email") or "").strip().lower()
        if not email:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google did not return an email address")
        return {
            "email": email,
            "name": (profile.get("name") or profile.get("given_name") or email.split("@", 1)[0]).strip(),
        }


async def _fetch_github_profile(code: str, redirect_uri: str) -> dict[str, str]:
    cfg = _provider_config("github")
    async with httpx.AsyncClient(timeout=20.0, headers={"Accept": "application/json", "User-Agent": "DeepShield"}) as client:
        token_res = await client.post(cfg["token_url"], data={
            "code": code,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": redirect_uri,
        }, headers={"Accept": "application/json", "User-Agent": "DeepShield"})
        token_res.raise_for_status()
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "GitHub OAuth token exchange failed")
        user_res = await client.get(cfg["userinfo_url"], headers={"Authorization": f"Bearer {access_token}"})
        user_res.raise_for_status()
        profile = user_res.json()
        email = (profile.get("email") or "").strip().lower()
        if not email:
            emails_res = await client.get(cfg.get("emails_url", ""), headers={"Authorization": f"Bearer {access_token}"})
            emails_res.raise_for_status()
            for item in emails_res.json():
                if item.get("primary") and item.get("verified") and item.get("email"):
                    email = str(item["email"]).strip().lower()
                    break
        if not email:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "GitHub did not return a verified email address")
        name = (profile.get("name") or profile.get("login") or email.split("@", 1)[0]).strip()
        return {"email": email, "name": name}


def _frontend_callback_url(path: str) -> str:
    base = settings.PUBLIC_APP_URL.strip().rstrip("/")
    return f"{base}{path}" if base else path


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        expires_in_minutes=settings.JWT_EXPIRATION_MINUTES,
        user=UserOut(id=user.id, email=user.email, name=user.name, created_at=user.created_at),
    )


@limiter.limit(ANON_AUTH_REGISTER)
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterBody, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = register_user(db, body.email, body.password, body.name)
    except IntegrityError:
        db.rollback()
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Registration rejected email={body.email} ip={client_host}")
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Registered user id={user.id} email={user.email} ip={client_host}")
    return _token_response(user)


@limiter.limit(ANON_AUTH_LOGIN)
@router.post("/login", response_model=TokenResponse)
def login(body: LoginBody, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(db, body.email, body.password)
    if not user:
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Login failed email={body.email} ip={client_host}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Login user id={user.id} email={user.email} ip={client_host}")
    return _token_response(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name, created_at=user.created_at)


@router.get("/oauth/{provider}/start")
def oauth_start(provider: str, request: Request, redirect_to: str = "/analyze", remember: bool = True) -> dict[str, str]:
    cfg = _provider_config(provider)
    if not cfg.get("client_id") or not cfg.get("client_secret"):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"{provider.title()} OAuth is not configured")

    callback_url = str(request.url_for("oauth_callback", provider=provider))
    state = _state_sign({
        "provider": provider.lower().strip(),
        "redirect_to": _normalize_redirect_path(redirect_to),
        "remember": bool(remember),
        "exp": int(datetime.now(timezone.utc).timestamp()) + _OAUTH_TTL_SECONDS,
    })

    if provider.lower().strip() == "google":
        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": cfg["scope"],
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    else:
        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": cfg["scope"],
            "allow_signup": "true",
            "state": state,
        }

    from urllib.parse import urlencode

    return {"authorization_url": f"{cfg['authorize_url']}?{urlencode(params)}"}


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(provider: str, code: str, state: str, request: Request, db: Session = Depends(get_db)):
    state_payload = _state_verify(state)
    if not state_payload or state_payload.get("provider") != provider.lower().strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")

    redirect_to = _normalize_redirect_path(str(state_payload.get("redirect_to") or "/analyze"))
    remember = bool(state_payload.get("remember", True))
    callback_url = str(request.url_for("oauth_callback", provider=provider))

    provider_key = provider.lower().strip()
    if provider_key == "google":
        profile = await _fetch_google_profile(code, callback_url)
    elif provider_key == "github":
        profile = await _fetch_github_profile(code, callback_url)
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unsupported OAuth provider")

    email = profile["email"].strip().lower()
    name = profile.get("name") or email.split("@", 1)[0]
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(32)), name=name)
        db.add(user)
    elif name and not user.name:
        user.name = name
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    frontend_url = _frontend_callback_url("/auth/callback")
    from urllib.parse import urlencode

    target = f"{frontend_url}?{urlencode({'token': token, 'next': redirect_to, 'remember': '1' if remember else '0'})}"
    return RedirectResponse(target, status_code=status.HTTP_302_FOUND)
