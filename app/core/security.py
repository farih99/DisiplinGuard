"""Utilitas hash password dan JWT untuk autentikasi DisiplinGuard."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Menghasilkan hash password tanpa menyimpan password asli."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password tidak boleh kosong.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password tidak boleh melebihi 72 byte untuk bcrypt.")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Memeriksa password terhadap hash yang tersimpan."""
    if not isinstance(plain, str) or not isinstance(hashed, str):
        return False
    if len(plain.encode("utf-8")) > 72:
        return False
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        # Hash rusak/tidak dikenali tidak boleh membuat endpoint login menjadi 500.
        return False


def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    subject = data.get("sub")
    if subject is None or str(subject).strip() == "":
        raise ValueError("Claim sub wajib diisi.")
    now = datetime.now(timezone.utc)
    # Hanya sub yang diterima dari pemanggil. Claim rahasia tidak disalin ke JWT.
    claims = {
        "sub": str(subject),
        "token_type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid4()),
    }
    return jwt.encode(
        claims,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def create_access_token(data: dict) -> str:
    return _create_token(
        data,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(data: dict) -> str:
    return _create_token(
        data,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict:
    """Memvalidasi signature, algoritma, dan expiry JWT."""
    payload = jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
    )
    if not isinstance(payload, dict) or not payload.get("sub"):
        raise JWTError("Token tidak memiliki subject yang valid.")
    return payload
