from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.student import Student


class StudentRepository:
    """Repository hanya menjalankan query untuk entitas Student."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_students(
        self, *, class_scopes: list[tuple[str, str]], offset: int, limit: int
    ) -> list[Student]:
        scope_filter = or_(*[
            and_(Student.class_name == class_name, Student.major == major)
            for class_name, major in class_scopes
        ])
        statement = (
            select(Student).where(scope_filter).order_by(Student.id).offset(offset).limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, student_id: int) -> Student | None:
        return self.db.get(Student, student_id)
