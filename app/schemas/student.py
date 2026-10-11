from pydantic import BaseModel, ConfigDict, Field


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_code: str
    name: str
    class_name: str
    major: str


class AttendanceSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    attendance_percentage: float = Field(ge=0, le=100)
    alpha_count: int = Field(ge=0)
    late_count: int = Field(ge=0)


class AcademicPerformanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    # TODO: [PTM-06] Tambahkan rentang nilai setelah dikonfirmasi oleh sekolah.
    average_score: float


class StudentDetailData(StudentRead):
    attendance: AttendanceSummaryRead | None = None
    academic: AcademicPerformanceRead | None = None


class StudentListResponse(BaseModel):
    data: list[StudentRead]


class StudentDetailResponse(BaseModel):
    data: StudentDetailData
