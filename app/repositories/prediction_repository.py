from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.student import Student


class PredictionRepository:
    """Repository hanya mengelola query/penyimpanan hasil prediksi."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, prediction_id: int) -> Prediction | None:
        return self.db.get(Prediction, prediction_id)

    def create(
        self,
        *,
        student_id: int,
        discipline_category: str,
        risk_score: float,
        recommendation: str,
    ) -> Prediction:
        prediction = Prediction(
            student_id=student_id,
            discipline_category=discipline_category,
            risk_score=risk_score,
            recommendation=recommendation,
        )
        try:
            self.db.add(prediction)
            self.db.commit()
            self.db.refresh(prediction)
            return prediction
        except Exception:
            self.db.rollback()
            raise

    def list_risk_students(
        self, *, class_scopes: list[tuple[str, str]], category: str | None = None, limit: int = 100
    ) -> list[tuple[Prediction, Student]]:
        # Ambil hasil terbaru tiap siswa, bukan semua riwayat prediksi.
        latest_ids = (
            select(
                Prediction.id.label("prediction_id"),
                func.row_number()
                .over(
                    partition_by=Prediction.student_id,
                    order_by=(Prediction.created_at.desc(), Prediction.id.desc()),
                )
                .label("row_number"),
            )
        ).subquery()
        scope_filter = or_(*[
            and_(Student.class_name == class_name, Student.major == major)
            for class_name, major in class_scopes
        ])
        statement = (
            select(Prediction, Student)
            .join(Student, Student.id == Prediction.student_id)
            .join(latest_ids, latest_ids.c.prediction_id == Prediction.id)
            .where(latest_ids.c.row_number == 1, scope_filter)
            .order_by(Prediction.risk_score.desc(), Prediction.created_at.desc())
            .limit(limit)
        )
        if category is not None:
            statement = statement.where(Prediction.discipline_category == category)
        return [(prediction, student) for prediction, student in self.db.execute(statement).all()]
