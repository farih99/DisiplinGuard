"""Environment testing agar tidak menggunakan secret atau database production."""
import os
import secrets

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/disiplinguard-auth-tests.db")
os.environ.setdefault("SECRET_KEY", secrets.token_urlsafe(48))
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("MODEL_PATH", "./models/test-model.joblib")
os.environ.setdefault("SCALER_PATH", "./models/test-scaler.joblib")
os.environ.setdefault("MAX_FILE_SIZE_MB", "10")

os.environ.setdefault("MAX_REQUEST_BODY_BYTES", "1048576")
os.environ.setdefault("API_RATE_LIMIT_REQUESTS", "120")
os.environ.setdefault("AUTH_RATE_LIMIT_REQUESTS", "20")
os.environ.setdefault("AI_RATE_LIMIT_REQUESTS", "10")
os.environ.setdefault("RATE_LIMIT_WINDOW_SECONDS", "60")
os.environ.setdefault("MAX_AI_COUNT", "366")
os.environ.setdefault("MAX_AVERAGE_SCORE", "100.0")
os.environ.setdefault("RISK_SCORE_MAX", "1.0")
