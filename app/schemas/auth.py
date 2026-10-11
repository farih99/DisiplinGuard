"""Schema request dan response autentikasi dengan Pydantic v2."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validate_bcrypt_length(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password tidak boleh melebihi 72 byte.")
    return value


class UserCreate(BaseModel):
    # Role tidak boleh diterima dari payload publik. Akun signup menjadi pending.
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_size(cls, value: str) -> str:
        return _validate_bcrypt_length(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_size(cls, value: str) -> str:
        return _validate_bcrypt_length(value)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
