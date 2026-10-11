from app.core.exceptions import EntityNotFoundError
from app.models.user import User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_class_assignment_repository import UserClassAssignmentRepository
from app.services.access_control import (
    ensure_staff_role,
    ensure_student_data_access,
    get_accessible_class_scopes,
)


class StudentService:
    """Aturan aplikasi monitoring siswa; query tetap berada di repository."""

    def __init__(
        self,
        *,
        student_repository: StudentRepository,
        attendance_repository: AttendanceRepository,
        academic_repository: AcademicRepository,
        assignment_repository: UserClassAssignmentRepository,
    ) -> None:
        self.student_repository = student_repository
        self.attendance_repository = attendance_repository
        self.academic_repository = academic_repository
        self.assignment_repository = assignment_repository

    def list_students(self, *, current_user: User, page: int, limit: int):
        scopes = get_accessible_class_scopes(current_user, self.assignment_repository)
        offset = (page - 1) * limit
        return self.student_repository.list_students(class_scopes=scopes, offset=offset, limit=limit)

    def get_student(self, student_id: int, *, current_user: User):
        ensure_staff_role(current_user)
        student = self.student_repository.get_by_id(student_id)
        if student is None:
            raise EntityNotFoundError("Siswa tidak ditemukan.")
        ensure_student_data_access(current_user, student, self.assignment_repository)
        return student

    def get_student_detail(self, student_id: int, *, current_user: User) -> dict:
        student = self.get_student(student_id, current_user=current_user)
        attendance = self.attendance_repository.get_latest_by_student_id(student_id)
        academic = self.academic_repository.get_latest_by_student_id(student_id)
        return {
            "id": student.id,
            "student_code": student.student_code,
            "name": student.name,
            "class_name": student.class_name,
            "major": student.major,
            "attendance": attendance,
            "academic": academic,
        }

    def get_attendance(self, student_id: int, *, current_user: User):
        self.get_student(student_id, current_user=current_user)
        attendance = self.attendance_repository.get_latest_by_student_id(student_id)
        if attendance is None:
            raise EntityNotFoundError("Data absensi siswa belum tersedia.")
        return attendance

    def get_academic(self, student_id: int, *, current_user: User):
        self.get_student(student_id, current_user=current_user)
        academic = self.academic_repository.get_latest_by_student_id(student_id)
        if academic is None:
            raise EntityNotFoundError("Data prestasi akademik siswa belum tersedia.")
        return academic
