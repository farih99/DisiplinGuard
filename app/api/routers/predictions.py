from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.rate_limit import ai_rate_limit, api_rate_limit
from app.api.deps import get_current_active_user, get_prediction_service
from app.core.exceptions import AccessDeniedError, AIUnavailableError, AITimeoutError, EntityNotFoundError
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.prediction import PredictionCreateRequest, PredictionRead, PredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["AI"], dependencies=[Depends(api_rate_limit)])


@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Memprediksi tingkat kedisiplinan siswa",
    dependencies=[Depends(ai_rate_limit)],
    responses={
        403: {"model": ErrorResponse, "description": "Pengguna tidak berwenang mengakses siswa"},
        503: {"model": ErrorResponse, "description": "AI_UNAVAILABLE atau AI_TIMEOUT"},
        404: {"description": "Siswa tidak ditemukan"},
    },
)
def create_prediction(
    payload: PredictionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    try:
        result = service.create_prediction(payload, current_user=current_user)
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "STUDENT_NOT_FOUND", "message": str(exc)}) from exc
    except AITimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "AI_TIMEOUT", "message": str(exc)}) from exc
    except AIUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "AI_UNAVAILABLE", "message": str(exc)}) from exc
    return PredictionResponse(data=PredictionRead.model_validate(result))


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Menampilkan hasil prediksi",
    responses={403: {"model": ErrorResponse, "description": "Pengguna tidak berwenang mengakses data"}},
)
def get_prediction(
    prediction_id: int = Path(gt=0),
    current_user: User = Depends(get_current_active_user),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    try:
        result = service.get_prediction(prediction_id, current_user=current_user)
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "PREDICTION_NOT_FOUND", "message": str(exc)}) from exc
    return PredictionResponse(data=PredictionRead.model_validate(result))
