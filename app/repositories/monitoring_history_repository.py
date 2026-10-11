from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monitoring_history import MonitoringHistory


class MonitoringHistoryRepository:
    """Repository khusus query dan penyimpanan riwayat pemantauan."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        student_id: int,
        user_id: int,
        follow_up: str,
        notes: str | None,
    ) -> MonitoringHistory:
        item = MonitoringHistory(
            student_id=student_id,
            user_id=user_id,
            follow_up=follow_up,
            notes=notes,
        )
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            raise

    def list_by_student_id(
        self, student_id: int, *, offset: int = 0, limit: int = 100
    ) -> list[MonitoringHistory]:
        statement = (
            select(MonitoringHistory)
            .where(MonitoringHistory.student_id == student_id)
            .order_by(MonitoringHistory.created_at.desc(), MonitoringHistory.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
