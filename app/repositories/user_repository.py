"""Repository untuk operasi database User."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def create(
        self, *, email: str, password_hash: str, role: str, is_active: bool = True
    ) -> User:
        user = User(email=email, password_hash=password_hash, role=role, is_active=is_active)
        self.db.add(user)
        self.db.flush()
        return user

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, user: User) -> None:
        self.db.refresh(user)
