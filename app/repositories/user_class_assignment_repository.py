"""Repository query penugasan kelas yang menjadi lingkup akses pengguna."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_class_assignment import UserClassAssignment


class UserClassAssignmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_scopes(self, user_id: int) -> list[tuple[str, str]]:
        statement = (
            select(UserClassAssignment.class_name, UserClassAssignment.major)
            .where(UserClassAssignment.user_id == user_id)
            .order_by(UserClassAssignment.class_name, UserClassAssignment.major)
        )
        return [(class_name, major) for class_name, major in self.db.execute(statement).all()]

    def has_scope(self, user_id: int, class_name: str, major: str) -> bool:
        statement = select(UserClassAssignment.id).where(
            UserClassAssignment.user_id == user_id,
            UserClassAssignment.class_name == class_name,
            UserClassAssignment.major == major,
        )
        return self.db.scalar(statement) is not None
