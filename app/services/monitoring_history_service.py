from app.core.exceptions import EntityNotFoundError
from app.models.user import User
from app.repositories.monitoring_history_repository import MonitoringHistoryRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_class_assignment_repository import UserClassAssignmentRepository
from app.services.access_control import ensure_staff_role, ensure_student_data_access


class MonitoringHistoryService:
    def __init__(
        self,
        repository: MonitoringHistoryRepository,
        student_repository: StudentRepository,
        assignment_repository: UserClassAssignmentRepository,
    ) -> None:
        self.repository = repository
        self.student_repository = student_repository
        self.assignment_repository = assignment_repository

    def _get_authorized_student(self, student_id: int, current_user: User):
        ensure_staff_role(current_user)
        student = self.student_repository.get_by_id(student_id)
        if student is None:
            raise EntityNotFoundError("Siswa tidak ditemukan.")
        ensure_student_data_access(current_user, student, self.assignment_repository)
        return student

    def create(self, *, current_user: User, student_id: int, follow_up: str, notes: str | None = None):
        self._get_authorized_student(student_id, current_user)
        return self.repository.create(
            student_id=student_id,
            user_id=current_user.id,
            follow_up=follow_up,
            notes=notes,
        )

    def list_by_student_id(
        self, student_id: int, *, current_user: User, offset: int = 0, limit: int = 100
    ):
        self._get_authorized_student(student_id, current_user)
        return self.repository.list_by_student_id(student_id, offset=offset, limit=min(limit, 100))
