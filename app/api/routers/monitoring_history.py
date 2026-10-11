from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.rate_limit import api_rate_limit
from app.api.deps import get_current_active_user, get_monitoring_history_service
from app.core.exceptions import AccessDeniedError, EntityNotFoundError
from app.models.user import User
from app.schemas.monitoring_history import (
    MonitoringHistoryCreateRequest,
    MonitoringHistoryListResponse,
    MonitoringHistoryRead,
    MonitoringHistoryResponse,
)
from app.services.monitoring_history_service import MonitoringHistoryService

router = APIRouter(prefix="/monitoring-history", tags=["Monitoring History"], dependencies=[Depends(api_rate_limit)])


@router.post("", response_model=MonitoringHistoryResponse, status_code=status.HTTP_201_CREATED, summary="Menyimpan riwayat pemantauan")
def create_monitoring_history(
    payload: MonitoringHistoryCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: MonitoringHistoryService = Depends(get_monitoring_history_service),
) -> MonitoringHistoryResponse:
    try:
        result = service.create(current_user=current_user, **payload.model_dump())
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "STUDENT_NOT_FOUND", "message": str(exc)}) from exc
    return MonitoringHistoryResponse(data=MonitoringHistoryRead.model_validate(result))


@router.get("/{student_id}", response_model=MonitoringHistoryListResponse, summary="Menampilkan riwayat pemantauan siswa")
def get_monitoring_history(
    student_id: int = Path(gt=0),
    offset: int = Query(default=0, ge=0, le=1_000_000),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: MonitoringHistoryService = Depends(get_monitoring_history_service),
) -> MonitoringHistoryListResponse:
    try:
        result = service.list_by_student_id(student_id, current_user=current_user, offset=offset, limit=limit)
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "STUDENT_NOT_FOUND", "message": str(exc)}) from exc
    return MonitoringHistoryListResponse(data=[MonitoringHistoryRead.model_validate(item) for item in result])
