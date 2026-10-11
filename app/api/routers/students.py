from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.rate_limit import api_rate_limit
from app.api.deps import get_current_active_user, get_student_service
from app.core.exceptions import AccessDeniedError, EntityNotFoundError
from app.models.user import User
from app.schemas.student import (
    AcademicPerformanceRead,
    AttendanceSummaryRead,
    StudentDetailData,
    StudentDetailResponse,
    StudentListResponse,
    StudentRead,
)
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"], dependencies=[Depends(api_rate_limit)])


def _raise_access_denied(exc: AccessDeniedError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("", response_model=StudentListResponse, summary="Menampilkan daftar siswa")
def list_students(
    page: int = Query(default=1, ge=1, le=10000),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: StudentService = Depends(get_student_service),
) -> StudentListResponse:
    try:
        students = service.list_students(current_user=current_user, page=page, limit=limit)
    except AccessDeniedError as exc:
        raise _raise_access_denied(exc) from exc
    return StudentListResponse(data=[StudentRead.model_validate(item) for item in students])


@router.get("/{student_id}", response_model=StudentDetailResponse, summary="Menampilkan detail siswa")
def get_student(
    student_id: int = Path(gt=0),
    current_user: User = Depends(get_current_active_user),
    service: StudentService = Depends(get_student_service),
) -> StudentDetailResponse:
    try:
        detail = service.get_student_detail(student_id, current_user=current_user)
    except AccessDeniedError as exc:
        raise _raise_access_denied(exc) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return StudentDetailResponse(data=StudentDetailData.model_validate(detail))


@router.get("/{student_id}/attendance", response_model=AttendanceSummaryRead, summary="Menampilkan indikator absensi siswa")
def get_student_attendance(
    student_id: int = Path(gt=0),
    current_user: User = Depends(get_current_active_user),
    service: StudentService = Depends(get_student_service),
) -> AttendanceSummaryRead:
    try:
        attendance = service.get_attendance(student_id, current_user=current_user)
    except AccessDeniedError as exc:
        raise _raise_access_denied(exc) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AttendanceSummaryRead.model_validate(attendance)


@router.get("/{student_id}/academic", response_model=AcademicPerformanceRead, summary="Menampilkan prestasi akademik siswa")
def get_student_academic(
    student_id: int = Path(gt=0),
    current_user: User = Depends(get_current_active_user),
    service: StudentService = Depends(get_student_service),
) -> AcademicPerformanceRead:
    try:
        academic = service.get_academic(student_id, current_user=current_user)
    except AccessDeniedError as exc:
        raise _raise_access_denied(exc) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AcademicPerformanceRead.model_validate(academic)
