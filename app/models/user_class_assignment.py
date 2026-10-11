"""Penugasan eksplisit pengguna ke kelas/jurusan untuk otorisasi level objek."""
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserClassAssignment(Base):
    __tablename__ = "user_class_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "class_name", "major", name="uq_user_class_assignment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    major: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
