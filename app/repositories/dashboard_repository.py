from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.student import Student


class DashboardRepository:
    """Repository hanya menjalankan query agregasi untuk dashboard."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary_data(self, *, class_scopes: list[tuple[str, str]]) -> dict[str, object]:
        scope_filter = or_(*[
            and_(Student.class_name == class_name, Student.major == major)
            for class_name, major in class_scopes
        ])
        total_students = int(
            self.db.scalar(select(func.count()).select_from(Student).where(scope_filter)) or 0
        )

        ranked_predictions = (
            select(
                Prediction.id.label("prediction_id"),
                Prediction.student_id.label("student_id"),
                Prediction.discipline_category.label("discipline_category"),
                func.row_number()
                .over(
                    partition_by=Prediction.student_id,
                    order_by=(Prediction.created_at.desc(), Prediction.id.desc()),
                )
                .label("row_number"),
            )
        ).subquery()

        counts_statement = (
            select(ranked_predictions.c.discipline_category, func.count())
            .join(Student, Student.id == ranked_predictions.c.student_id)
            .where(ranked_predictions.c.row_number == 1, scope_filter)
            .group_by(ranked_predictions.c.discipline_category)
        )
        category_rows = self.db.execute(counts_statement).all()
        category_counts = {"tinggi": 0, "sedang": 0, "rendah": 0}
        for category, count in category_rows:
            if category in category_counts:
                category_counts[category] = int(count)

        with_prediction = sum(category_counts.values())
        # TODO: [PTM-06] Konfirmasi metrik dashboard final kepada pemilik produk.
        return {
            "total_students": total_students,
            "students_with_prediction": with_prediction,
            "students_without_prediction": max(0, total_students - with_prediction),
            "discipline_categories": category_counts,
        }
