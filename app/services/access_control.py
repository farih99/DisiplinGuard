"""Kontrol akses per role dan per objek/kelas untuk mencegah BOLA."""
from app.core.exceptions import AccessDeniedError
from app.models.student import Student
from app.models.user import User
from app.repositories.user_class_assignment_repository import UserClassAssignmentRepository

_ALLOWED_STAFF_ROLES = {"guru_bk", "wali_kelas"}


def ensure_staff_role(user: User) -> None:
    role = (user.role or "").strip().lower().replace(" ", "_").replace("-", "_")
    if role not in _ALLOWED_STAFF_ROLES:
        raise AccessDeniedError("Pengguna tidak berwenang mengakses data kedisiplinan siswa.")


def get_accessible_class_scopes(
    user: User,
    assignment_repository: UserClassAssignmentRepository,
) -> list[tuple[str, str]]:
    """Mengembalikan scope kelas; default deny jika role atau penugasan tidak valid.

    # TODO: [PTM-06] Tim sekolah perlu menyediakan proses provisioning assignment.
    # Kebijakan ini membatasi semua role staf ke kelas/jurusan yang ditugaskan.
    """
    ensure_staff_role(user)
    scopes = assignment_repository.list_scopes(user.id)
    if not scopes:
        raise AccessDeniedError("Pengguna belum memiliki penugasan kelas yang dapat diakses.")
    return scopes


def ensure_student_data_access(
    user: User,
    student: Student,
    assignment_repository: UserClassAssignmentRepository,
) -> None:
    """Menolak akses kecuali student termasuk kelas/jurusan yang ditugaskan."""
    scopes = get_accessible_class_scopes(user, assignment_repository)
    if (student.class_name, student.major) not in set(scopes):
        raise AccessDeniedError("Pengguna tidak berwenang mengakses siswa tersebut.")
