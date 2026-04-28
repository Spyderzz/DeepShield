from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must include a lowercase letter")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must include an uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must include a digit")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("Password must include a symbol")
        return value


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserOut
