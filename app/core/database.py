from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.base import Base

_database_url = settings.database_url
_engine_options: dict[str, object] = {"pool_pre_ping": True}
if _database_url.startswith("sqlite"):
    # SQLite membutuhkan opsi ini untuk akses dari request/thread berbeda pada prototype.
    _engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(_database_url, **_engine_options)
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency generator: satu session per request dan selalu ditutup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db_for_prototype() -> None:
    """Membuat tabel untuk prototipe lokal; production sebaiknya memakai migration."""
    # Import metadata model agar seluruh tabel terdaftar pada Base.metadata.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
