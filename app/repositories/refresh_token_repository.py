"""Repository refresh token. Token mentah tidak disimpan, hanya JTI."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token_session import RefreshTokenSession


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_jti(self, jti: str) -> RefreshTokenSession | None:
        return self.db.scalar(select(RefreshTokenSession).where(RefreshTokenSession.jti == jti).with_for_update())

    def create(self, *, user_id: int, jti: str, expires_at: datetime) -> RefreshTokenSession:
        session = RefreshTokenSession(user_id=user_id, jti=jti, expires_at=expires_at)
        self.db.add(session)
        self.db.flush()
        return session

    def revoke(self, session: RefreshTokenSession, *, revoked_at: datetime) -> None:
        session.revoked_at = revoked_at
        self.db.add(session)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
