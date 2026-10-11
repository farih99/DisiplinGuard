from datetime import datetime
from decimal import Decimal
from enum import Enum
import math

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings
from app.core.input_sanitization import require_finite_number, sanitize_text


class DisciplineCategory(str, Enum):
    tinggi = "tinggi"
    sedang = "sedang"
    rendah = "rendah"


class PredictionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: int = Field(gt=0, strict=True)
    attendance_percentage: float = Field(ge=0, le=100, allow_inf_nan=False)
    alpha_count: int = Field(ge=0, le=settings.max_ai_count, strict=True)
    late_count: int = Field(ge=0, le=settings.max_ai_count, strict=True)
    # [ASUMSI-16] Skala nilai 0-100. Atur MAX_AVERAGE_SCORE bila kebijakan sekolah berbeda.
    average_score: float = Field(ge=0, le=settings.max_average_score, allow_inf_nan=False)

    @field_validator("attendance_percentage", "average_score", mode="before")
    @classmethod
    def validate_finite_numeric_fields(cls, value: object, info) -> float:
        number = require_finite_number(value, field_name=info.field_name)
        return number

    @field_validator("alpha_count", "late_count", mode="before")
    @classmethod
    def validate_integer_counts(cls, value: object, info) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{info.field_name} harus berupa bilangan bulat.")
        if value < 0 or value > settings.max_ai_count:
            raise ValueError(f"{info.field_name} harus berada pada rentang 0-{settings.max_ai_count}.")
        return value


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    discipline_category: DisciplineCategory
    risk_score: Decimal
    recommendation: str
    created_at: datetime


class PredictionResponse(BaseModel):
    data: PredictionRead


class PriorityStudentRead(BaseModel):
    student_id: int
    student_code: str
    student_name: str
    class_name: str
    major: str
    discipline_category: DisciplineCategory
    risk_score: Decimal
    recommendation: str
    prediction_id: int
    predicted_at: datetime


class PriorityStudentListResponse(BaseModel):
    data: list[PriorityStudentRead]
