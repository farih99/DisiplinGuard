"""Service autentikasi, termasuk hash password dan rotasi refresh token."""
from datetime import datetime, timezone

from jose import JWTError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, TokenRefresh, UserCreate, UserLogin


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    @staticmethod
    def _normalise_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _new_token_pair(user_id: int) -> tuple[str, str]:
        claims = {"sub": str(user_id)}
        return create_access_token(claims), create_refresh_token(claims)

    def _store_refresh_token(self, user_id: int, refresh_token: str) -> None:
        claims = decode_token(refresh_token)
        expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc)
        self.refresh_token_repository.create(
            user_id=user_id,
            jti=str(claims["jti"]),
            expires_at=expires_at,
        )

    def signup(self, payload: UserCreate) -> User:
        email = self._normalise_email(str(payload.email))
        if self.user_repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError

        try:
            user = self.user_repository.create(
                email=email,
                password_hash=hash_password(payload.password),
                # Pencegahan privilege escalation: akun publik selalu pending/nonaktif.
                # TODO: [PTM-06] Tambahkan provisioning staf melalui proses admin tepercaya.
                role="pending",
                is_active=False,
            )
            self.user_repository.commit()
            self.user_repository.refresh(user)
        except IntegrityError as exc:
            self.user_repository.rollback()
            raise EmailAlreadyRegisteredError from exc
        return user

    def login(self, payload: UserLogin) -> Token:
        email = self._normalise_email(str(payload.email))
        user = self.user_repository.get_by_email(email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError
        if not user.is_active:
            raise InactiveUserError

        access_token, refresh_token = self._new_token_pair(user.id)
        try:
            self._store_refresh_token(user.id, refresh_token)
            self.refresh_token_repository.commit()
        except Exception:
            self.refresh_token_repository.rollback()
            raise
        return Token(access_token=access_token, refresh_token=refresh_token)

    def refresh(self, payload: TokenRefresh) -> Token:
        try:
            claims = decode_token(payload.refresh_token)
            if claims.get("token_type") != "refresh":
                raise InvalidRefreshTokenError
            user_id = int(claims.get("sub", ""))
            jti = str(claims.get("jti", ""))
        except (JWTError, TypeError, ValueError) as exc:
            raise InvalidRefreshTokenError from exc

        if not jti:
            raise InvalidRefreshTokenError
        session = self.refresh_token_repository.get_by_jti(jti)
        user = self.user_repository.get_by_id(user_id)
        if (
            session is None
            or session.user_id != user_id
            or session.revoked_at is not None
            or user is None
        ):
            raise InvalidRefreshTokenError
        if not user.is_active:
            raise InactiveUserError

        access_token, new_refresh_token = self._new_token_pair(user.id)
        try:
            # Rotasi dibuat satu transaksi supaya token lama tidak dapat dipakai ulang.
            self.refresh_token_repository.revoke(session, revoked_at=datetime.now(timezone.utc))
            self._store_refresh_token(user.id, new_refresh_token)
            self.refresh_token_repository.commit()
        except Exception:
            self.refresh_token_repository.rollback()
            raise
        return Token(access_token=access_token, refresh_token=new_refresh_token)

    @staticmethod
    def get_me(user: User) -> User:
        return user
