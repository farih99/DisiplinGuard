"""Router autentikasi untuk signup, login, refresh, dan profil."""
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError

from app.api.deps import get_auth_service, get_current_active_user
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.models.user import User
from app.schemas.auth import Token, TokenRefresh, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService
from app.core.rate_limit import api_rate_limit, auth_rate_limit

router = APIRouter(prefix="/auth", tags=["Auth"], dependencies=[Depends(api_rate_limit)])


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
    summary="Mendaftarkan akun pengguna",
    dependencies=[Depends(auth_rate_limit)],
)
def signup(payload: UserCreate, service: AuthService = Depends(get_auth_service)) -> User:
    try:
        return service.signup(payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar.") from exc


@router.post(
    "/login",
    response_model=Token,
    summary="Login dan menerbitkan token",
    dependencies=[Depends(auth_rate_limit)],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["email", "password"],
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "password": {"type": "string", "minLength": 1, "maxLength": 128},
                        },
                    }
                },
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "required": ["username", "password"],
                        "properties": {
                            "username": {
                                "type": "string",
                                "format": "email",
                                "description": "Isi username dengan alamat email pengguna.",
                            },
                            "password": {"type": "string"},
                        },
                    }
                },
            },
        }
    },
)
async def login(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """Menerima JSON biasa dan form OAuth2 untuk kompatibilitas Swagger UI."""
    content_type = request.headers.get("content-type", "").lower()
    try:
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            # OAuth2 Password Flow menggunakan nama field 'username'; nilainya berupa email.
            payload = UserLogin(
                email=form.get("username") or form.get("email"),
                password=form.get("password"),
            )
        else:
            body = await request.json()
            payload = UserLogin.model_validate(body)
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            details = [
                {"loc": ["body", *err.get("loc", ())], "msg": err["msg"], "type": err["type"]}
                for err in exc.errors()
            ]
        else:
            details = "Body login tidak valid. Kirim JSON atau form dengan email/username dan password."
        raise HTTPException(status_code=422, detail=details) from exc

    try:
        return service.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=401,
            detail="Email atau password tidak valid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(status_code=403, detail="Akun tidak aktif.") from exc


@router.post(
    "/refresh", response_model=Token,
    summary="Memperbarui token menggunakan refresh token",
    dependencies=[Depends(auth_rate_limit)],
)
def refresh(payload: TokenRefresh, service: AuthService = Depends(get_auth_service)) -> Token:
    try:
        return service.refresh(payload)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail="Refresh token tidak valid, kedaluwarsa, atau sudah digunakan.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(status_code=403, detail="Akun tidak aktif.") from exc


@router.get("/me", response_model=UserResponse, summary="Menampilkan profil pengguna aktif")
def me(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> User:
    return service.get_me(current_user)
