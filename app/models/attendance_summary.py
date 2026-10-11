from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AttendanceSummary(Base):
    __tablename__ = "attendance_summaries"
    __table_args__ = (
        CheckConstraint("attendance_percentage >= 0 AND attendance_percentage <= 100", name="ck_attendance_percentage_range"),
        CheckConstraint("alpha_count >= 0", name="ck_alpha_count_nonnegative"),
        CheckConstraint("late_count >= 0", name="ck_late_count_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    alpha_count: Mapped[int] = mapped_column(Integer, nullable=False)
    late_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
