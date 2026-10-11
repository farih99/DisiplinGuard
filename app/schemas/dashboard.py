from pydantic import BaseModel, Field


class DisciplineCategoryCounts(BaseModel):
    tinggi: int = Field(ge=0)
    sedang: int = Field(ge=0)
    rendah: int = Field(ge=0)


class DashboardSummaryData(BaseModel):
    total_students: int = Field(ge=0)
    students_with_prediction: int = Field(ge=0)
    students_without_prediction: int = Field(ge=0)
    discipline_categories: DisciplineCategoryCounts


class DashboardSummaryResponse(BaseModel):
    data: DashboardSummaryData
