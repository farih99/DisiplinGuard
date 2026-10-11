from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_performance import AcademicPerformance


class AcademicRepository:
    """Repository khusus query prestasi akademik."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_by_student_id(self, student_id: int) -> AcademicPerformance | None:
        # TODO: [PTM-06] Pastikan periode nilai yang digunakan untuk prediksi disepakati tim/sekolah.
        statement = (
            select(AcademicPerformance)
            .where(AcademicPerformance.student_id == student_id)
            .order_by(AcademicPerformance.recorded_at.desc(), AcademicPerformance.id.desc())
            .limit(1)
        )
        return self.db.scalars(statement).first()
