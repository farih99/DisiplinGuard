from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.input_sanitization import sanitize_text


class MonitoringHistoryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: int = Field(gt=0, strict=True)
    follow_up: str = Field(min_length=1, max_length=5000)
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("follow_up")
    @classmethod
    def clean_follow_up(cls, value: str) -> str:
        return sanitize_text(value, max_length=5000)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return sanitize_text(value, max_length=10000, allow_empty=True)


class MonitoringHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    user_id: int | None
    follow_up: str
    notes: str | None
    created_at: datetime


class MonitoringHistoryResponse(BaseModel):
    data: MonitoringHistoryRead


class MonitoringHistoryListResponse(BaseModel):
    data: list[MonitoringHistoryRead]
