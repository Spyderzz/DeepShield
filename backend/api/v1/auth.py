from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.deps import get_current_user
from config import settings
from db.database import get_db
from db.models import User
from schemas.auth import LoginBody, RegisterBody, TokenResponse, UserOut
from services.auth_service import authenticate, create_access_token, register_user
from services.rate_limit import ANON_AUTH_LOGIN, ANON_AUTH_REGISTER, limiter

router = APIRouter(prefix="/auth", tags=["auth"])


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
