from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance_summary import AttendanceSummary


class AttendanceRepository:
    """Repository khusus query ringkasan absensi."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_by_student_id(self, student_id: int) -> AttendanceSummary | None:
        # TODO: [PTM-06] Pastikan pemilihan record terbaru sesuai periode akademik yang disepakati.
        statement = (
            select(AttendanceSummary)
            .where(AttendanceSummary.student_id == student_id)
            .order_by(AttendanceSummary.recorded_at.desc(), AttendanceSummary.id.desc())
            .limit(1)
        )
        return self.db.scalars(statement).first()
