import math
from decimal import Decimal, InvalidOperation

from app.core.exceptions import AIUnavailableError, EntityNotFoundError
from app.core.input_sanitization import sanitize_text
from app.models.user import User
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_class_assignment_repository import UserClassAssignmentRepository
from app.schemas.prediction import PredictionCreateRequest, DisciplineCategory
from app.services.access_control import ensure_staff_role, ensure_student_data_access
from app.services.ai_inference_service import AIInferenceService


class PredictionService:
    """Orkestrasi otorisasi objek, inference, dan penyimpanan prediksi."""

    def __init__(
        self,
        *,
        student_repository: StudentRepository,
        prediction_repository: PredictionRepository,
        assignment_repository: UserClassAssignmentRepository,
        ai_service: AIInferenceService,
    ) -> None:
        self.student_repository = student_repository
        self.prediction_repository = prediction_repository
        self.assignment_repository = assignment_repository
        self.ai_service = ai_service

    def create_prediction(self, payload: PredictionCreateRequest, *, current_user: User):
        ensure_staff_role(current_user)
        student = self.student_repository.get_by_id(payload.student_id)
        if student is None:
            raise EntityNotFoundError("Siswa tidak ditemukan.")
        ensure_student_data_access(current_user, student, self.assignment_repository)

        # TODO: [PTM-06] Cocokkan input dengan indikator historis yang berwenang jika
        # kontrak produk diputuskan memakai data canonical dari database.
        inference = self.ai_service.predict(payload)
        category = inference.get("discipline_category")
        raw_risk_score = inference.get("risk_score")
        raw_recommendation = inference.get("recommendation")

        if category not in {item.value for item in DisciplineCategory}:
            raise AIUnavailableError("Model AI menghasilkan kategori yang tidak valid.")
        try:
            risk_decimal = Decimal(str(raw_risk_score))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise AIUnavailableError("Model AI menghasilkan skor risiko yang tidak valid.") from exc
        # [ASUMSI-17] Skor risiko mengikuti contoh API 0-1; ubah bersama schema/DB bila keputusan final berbeda.
        if not risk_decimal.is_finite() or risk_decimal < 0 or risk_decimal > Decimal("1.0"):
            raise AIUnavailableError("Skor risiko berada di luar rentang 0-1 yang dikonfigurasi.")
        if not isinstance(raw_recommendation, str):
            raise AIUnavailableError("Model AI belum menghasilkan rekomendasi yang valid.")
        try:
            recommendation = sanitize_text(raw_recommendation, max_length=5000)
        except ValueError as exc:
            raise AIUnavailableError("Model AI menghasilkan rekomendasi yang tidak valid.") from exc

        return self.prediction_repository.create(
            student_id=payload.student_id,
            discipline_category=category,
            risk_score=float(risk_decimal),
            recommendation=recommendation,
        )

    def get_prediction(self, prediction_id: int, *, current_user: User):
        ensure_staff_role(current_user)
        prediction = self.prediction_repository.get_by_id(prediction_id)
        if prediction is None:
            raise EntityNotFoundError("Hasil prediksi tidak ditemukan.")
        # Anti-BOLA: otorisasi dilakukan terhadap siswa yang terikat ke prediksi.
        student = self.student_repository.get_by_id(prediction.student_id)
        if student is None:
            raise EntityNotFoundError("Siswa yang terkait dengan prediksi tidak ditemukan.")
        ensure_student_data_access(current_user, student, self.assignment_repository)
        return prediction
