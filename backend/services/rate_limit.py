"""Phase 15.2 — Rate limiting via slowapi.

Exposes a shared `limiter` plus a request key function that differentiates
authenticated users (keyed by user id) from anonymous clients (keyed by IP).

slowapi 0.1.9 calls `exempt_when()` with no arguments, so we stash the current
Request in a ContextVar via a middleware (`RateLimitContextMiddleware`) and
read from it inside the exempt predicates.
"""
from __future__ import annotations

from contextvars import ContextVar

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from services.auth_service import decode_token

_REQUEST_STASH: ContextVar[Request | None] = ContextVar("_REQUEST_STASH", default=None)


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def _authed_user_id(request: Request) -> str | None:
    token = _bearer(request)
    if not token:
        return None
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    return str(payload["sub"])


def request_key(request: Request) -> str:
    """Keyed on user id when authed, IP address otherwise."""
    uid = _authed_user_id(request)
    if uid:
        return f"user:{uid}"
    return f"ip:{get_remote_address(request)}"


def is_authed() -> bool:
    request = _REQUEST_STASH.get()
    if request is None:
        return False
    return _authed_user_id(request) is not None


def is_anon() -> bool:
    request = _REQUEST_STASH.get()
    if request is None:
        return True
    return _authed_user_id(request) is None


class RateLimitContextMiddleware(BaseHTTPMiddleware):
    """Stashes the incoming Request in a ContextVar so slowapi's no-arg
    `exempt_when` predicates can read it."""

    async def dispatch(self, request: Request, call_next):
        token = _REQUEST_STASH.set(request)
        try:
            return await call_next(request)
        finally:
            _REQUEST_STASH.reset(token)


# Per-route rate limits — anon gets strict caps, authed gets generous quotas.
ANON_ANALYZE = "5/hour"
AUTH_ANALYZE = "50/hour"
ANON_REPORT = "2/hour"
AUTH_REPORT = "20/hour"

limiter = Limiter(
    key_func=request_key,
    default_limits=[],
    headers_enabled=True,
    enabled=True,
)
