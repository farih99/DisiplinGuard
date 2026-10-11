from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.rate_limit import api_rate_limit
from app.api.deps import get_current_active_user, get_priority_service
from app.core.exceptions import AccessDeniedError
from app.models.user import User
from app.schemas.prediction import PriorityStudentListResponse, PriorityStudentRead
from app.services.priority_student_service import PriorityStudentService

router = APIRouter(prefix="/priority-students", tags=["Priority"], dependencies=[Depends(api_rate_limit)])


@router.get("", response_model=PriorityStudentListResponse, summary="Menampilkan daftar prioritas siswa berisiko")
def list_priority_students(
    category: str | None = Query(default=None, pattern="^(tinggi|sedang|rendah)$"),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: PriorityStudentService = Depends(get_priority_service),
) -> PriorityStudentListResponse:
    try:
        result = service.list_priority_students(current_user=current_user, category=category, limit=limit)
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return PriorityStudentListResponse(data=[PriorityStudentRead.model_validate(item) for item in result])
