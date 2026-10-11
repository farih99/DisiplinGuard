from functools import lru_cache

from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurasi aplikasi dibaca dari environment atau file .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DisiplinGuard API"
    api_prefix: str = "/api"

    # Nilai sensitif/lingkungan tidak ditetapkan di source code.
    database_url: str
    secret_key: SecretStr
    algorithm: str
    access_token_expire_minutes: int = Field(gt=0)
    refresh_token_expire_days: int = Field(gt=0)
    model_path: str
    scaler_path: str
    max_file_size_mb: int = Field(gt=0)
    # Batas defensif untuk endpoint/resource. Sesuaikan berdasarkan data operasional.
    max_request_body_bytes: int = Field(default=1_048_576, gt=0)
    api_rate_limit_requests: int = Field(default=120, gt=0)
    auth_rate_limit_requests: int = Field(default=5, gt=0)
    ai_rate_limit_requests: int = Field(default=10, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)
    # [ASUMSI-15] Batas hitungan luas untuk satu agregat/periode input AI.
    max_ai_count: int = Field(default=366, gt=0)
    # [ASUMSI-16] Skala nilai sekolah diasumsikan 0-100 sampai dikonfirmasi.
    max_average_score: float = Field(default=100.0, gt=0)

    @field_validator("algorithm")
    @classmethod
    def enforce_hs256(cls, value: str) -> str:
        # Algoritma dikunci sesuai kontrak JWT proyek, bukan bebas dari konfigurasi operator.
        if value != "HS256":
            raise ValueError("ALGORITHM harus HS256 sesuai kebijakan JWT DisiplinGuard.")
        return value

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: SecretStr) -> SecretStr:
        # Mencegah aplikasi berjalan memakai placeholder dari .env.example.
        secret = value.get_secret_value()
        if "REPLACE_WITH" in secret.upper() or len(secret) < 32:
            raise ValueError("SECRET_KEY harus berupa secret acak dengan panjang minimal 32 karakter.")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
