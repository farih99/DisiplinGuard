"""Regression tests: hasil query hanya mencakup kelas/jurusan yang ditugaskan."""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base, Prediction, Student, User, UserClassAssignment
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.student_repository import StudentRepository


def test_repository_queries_are_scoped_to_assigned_class_and_major():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            user = User(
                email="wali@example.test", password_hash="not-used-in-this-test",
                role="wali_kelas", is_active=True,
            )
            own = Student(student_code="S001", name="Siswa A", class_name="X TKJ 1", major="TKJ")
            other = Student(student_code="S002", name="Siswa B", class_name="XI RPL 2", major="RPL")
            db.add_all([user, own, other])
            db.flush()
            db.add(UserClassAssignment(user_id=user.id, class_name="X TKJ 1", major="TKJ"))
            db.add_all([
                Prediction(student_id=own.id, discipline_category="rendah", risk_score=0.8, recommendation="Pantau"),
                Prediction(student_id=other.id, discipline_category="tinggi", risk_score=0.9, recommendation="Pantau"),
            ])
            db.commit()

            students = StudentRepository(db).list_students(
                class_scopes=[("X TKJ 1", "TKJ")], offset=0, limit=100
            )
            assert [item.student_code for item in students] == ["S001"]

            priorities = PredictionRepository(db).list_risk_students(
                class_scopes=[("X TKJ 1", "TKJ")], limit=100
            )
            assert len(priorities) == 1
            assert priorities[0][1].student_code == "S001"

            summary = DashboardRepository(db).get_summary_data(
                class_scopes=[("X TKJ 1", "TKJ")]
            )
            assert summary["total_students"] == 1
            assert summary["discipline_categories"]["rendah"] == 1
            assert summary["discipline_categories"]["tinggi"] == 0
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
