from fastapi import APIRouter, Depends, HTTPException, status

from app.core.rate_limit import api_rate_limit
from app.api.deps import get_current_active_user, get_dashboard_service
from app.core.exceptions import AccessDeniedError
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(api_rate_limit)])


@router.get("/summary", response_model=DashboardSummaryResponse, summary="Menampilkan ringkasan kondisi kedisiplinan")
def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    try:
        result = service.get_summary(current_user=current_user)
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return DashboardSummaryResponse(data=result)
