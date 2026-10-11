"""Pengujian validasi input angka AI dan sanitasi teks."""
import math

import pytest
from pydantic import ValidationError

from app.core.input_sanitization import require_finite_number, sanitize_text
from app.schemas.prediction import PredictionCreateRequest
from app.schemas.monitoring_history import MonitoringHistoryCreateRequest


def valid_payload(**updates):
    payload = {
        "student_id": 10,
        "attendance_percentage": 92.5,
        "alpha_count": 2,
        "late_count": 3,
        "average_score": 84.0,
    }
    payload.update(updates)
    return payload


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, "92.5"])
def test_require_finite_number_rejects_non_numeric_or_non_finite(value):
    with pytest.raises(ValueError):
        require_finite_number(value, field_name="value")


def test_ai_schema_accepts_valid_edge_values():
    payload = PredictionCreateRequest.model_validate(valid_payload(
        attendance_percentage=100.0, alpha_count=0, late_count=0, average_score=100.0
    ))
    assert payload.attendance_percentage == 100.0


@pytest.mark.parametrize("updates", [
    {"attendance_percentage": -0.1},
    {"attendance_percentage": 100.1},
    {"attendance_percentage": float("nan")},
    {"alpha_count": -1},
    {"alpha_count": 367},
    {"late_count": -1},
    {"late_count": 367},
    {"average_score": -1},
    {"average_score": 100.1},
    {"average_score": float("inf")},
    {"junk": "unexpected"},
])
def test_ai_schema_rejects_invalid_numeric_ranges(updates):
    with pytest.raises(ValidationError):
        PredictionCreateRequest.model_validate(valid_payload(**updates))


def test_sanitize_text_removes_control_characters():
    assert sanitize_text(" Pembinaan\r\n siswa\x00 perlu dipantau ", max_length=100) == "Pembinaan siswa perlu dipantau"


def test_monitoring_text_gets_sanitized():
    result = MonitoringHistoryCreateRequest.model_validate({
        "student_id": 2,
        "follow_up": "Panggil\r\nsiswa\x00 untuk konsultasi",
        "notes": "catatan\x07 lanjut",
    })
    assert "\r" not in result.follow_up and "\n" not in result.follow_up
    assert "\x00" not in result.follow_up
    assert result.follow_up == "Panggil siswa untuk konsultasi"


def test_prediction_result_validation_rejects_out_of_range_risk_score():
    from types import SimpleNamespace
    from app.core.exceptions import AIUnavailableError
    from app.services.prediction_service import PredictionService

    class Students:
        def get_by_id(self, student_id):
            return SimpleNamespace(id=student_id, class_name="X TKJ 1", major="TKJ")

    class Assignments:
        def list_scopes(self, user_id):
            return [("X TKJ 1", "TKJ")]

    class Predictions:
        def create(self, **kwargs):
            raise AssertionError("Hasil tidak valid tidak boleh disimpan")

    class BadAI:
        def predict(self, payload):
            return {"discipline_category": "tinggi", "risk_score": float("nan"), "recommendation": "Tindak lanjut"}

    service = PredictionService(
        student_repository=Students(),
        prediction_repository=Predictions(),
        assignment_repository=Assignments(),
        ai_service=BadAI(),
    )
    user = SimpleNamespace(id=4, role="guru_bk")
    payload = PredictionCreateRequest.model_validate(valid_payload())
    with pytest.raises(AIUnavailableError):
        service.create_prediction(payload, current_user=user)
