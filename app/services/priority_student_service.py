from app.models.user import User
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.user_class_assignment_repository import UserClassAssignmentRepository
from app.services.access_control import get_accessible_class_scopes


class PriorityStudentService:
    def __init__(
        self,
        prediction_repository: PredictionRepository,
        assignment_repository: UserClassAssignmentRepository,
    ) -> None:
        self.prediction_repository = prediction_repository
        self.assignment_repository = assignment_repository

    def list_priority_students(
        self, *, current_user: User, category: str | None = None, limit: int = 100
    ) -> list[dict[str, object]]:
        scopes = get_accessible_class_scopes(current_user, self.assignment_repository)
        rows = self.prediction_repository.list_risk_students(
            class_scopes=scopes, category=category, limit=min(limit, 100)
        )
        return [
            {
                "student_id": student.id,
                "student_code": student.student_code,
                "student_name": student.name,
                "class_name": student.class_name,
                "major": student.major,
                "discipline_category": prediction.discipline_category,
                "risk_score": prediction.risk_score,
                "recommendation": prediction.recommendation,
                "prediction_id": prediction.id,
                "predicted_at": prediction.created_at,
            }
            for prediction, student in rows
        ]
