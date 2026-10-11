from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.user_class_assignment_repository import UserClassAssignmentRepository
from app.services.access_control import get_accessible_class_scopes


class DashboardService:
    def __init__(
        self, repository: DashboardRepository, assignment_repository: UserClassAssignmentRepository
    ) -> None:
        self.repository = repository
        self.assignment_repository = assignment_repository

    def get_summary(self, *, current_user: User) -> dict[str, object]:
        scopes = get_accessible_class_scopes(current_user, self.assignment_repository)
        return self.repository.get_summary_data(class_scopes=scopes)
