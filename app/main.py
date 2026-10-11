from fastapi import FastAPI

from app.api.routers import (
    auth,
    dashboard,
    monitoring_history,
    predictions,
    priority_students,
    students,
)
from app.core.config import settings
from app.middleware.request_size_limit import RequestBodyLimitMiddleware

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend DisiplinGuard. Beberapa endpoint masih berupa scaffold PTM-06.",
)

# Prefix API disimpan dalam konfigurasi agar dapat disesuaikan melalui environment.
app.include_router(students.router, prefix=settings.api_prefix)
app.include_router(predictions.router, prefix=settings.api_prefix)
app.include_router(priority_students.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(monitoring_history.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)


# Batasi body aktual, termasuk request chunked tanpa Content-Length.
app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=settings.max_request_body_bytes)
