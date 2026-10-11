"""Dependency injection untuk database, service, dan autentikasi Bearer."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.monitoring_history_repository import MonitoringHistoryRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_class_assignment_repository import UserClassAssignmentRepository
from app.services.ai_inference_service import AIInferenceService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.monitoring_history_service import MonitoringHistoryService
from app.services.priority_student_service import PriorityStudentService
from app.services.prediction_service import PredictionService
from app.services.student_service import StudentService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_student_service(db: Session = Depends(get_db)) -> StudentService:
    return StudentService(
        student_repository=StudentRepository(db),
        attendance_repository=AttendanceRepository(db),
        academic_repository=AcademicRepository(db),
        assignment_repository=UserClassAssignmentRepository(db),
    )


def get_prediction_service(db: Session = Depends(get_db)) -> PredictionService:
    return PredictionService(
        student_repository=StudentRepository(db),
        prediction_repository=PredictionRepository(db),
        assignment_repository=UserClassAssignmentRepository(db),
        ai_service=AIInferenceService(),
    )


def get_priority_service(db: Session = Depends(get_db)) -> PriorityStudentService:
    return PriorityStudentService(
        PredictionRepository(db), UserClassAssignmentRepository(db)
    )


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(
        DashboardRepository(db), UserClassAssignmentRepository(db)
    )


def get_monitoring_history_service(db: Session = Depends(get_db)) -> MonitoringHistoryService:
    return MonitoringHistoryService(
        repository=MonitoringHistoryRepository(db),
        student_repository=StudentRepository(db),
        assignment_repository=UserClassAssignmentRepository(db),
    )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(
        user_repository=UserRepository(db),
        refresh_token_repository=RefreshTokenRepository(db),
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = decode_token(token)
        if claims.get("token_type") != "access":
            raise credentials_error
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.isdigit():
            raise credentials_error
        user_id = int(subject)
    except (JWTError, TypeError, ValueError) as exc:
        raise credentials_error from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise credentials_error
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Akun tidak aktif.")
    return current_user
