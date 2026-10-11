class EntityNotFoundError(Exception):
    """Entitas yang diminta tidak ditemukan."""


class AIUnavailableError(Exception):
    """Layanan/model AI belum tersedia atau gagal dimuat."""


class AITimeoutError(Exception):
    """Inferensi AI melewati batas waktu yang ditetapkan."""


class FeatureNotImplementedError(Exception):
    """Fitur masih menunggu implementasi pada PTM-06."""


class EmailAlreadyRegisteredError(Exception):
    """Email sudah terdaftar."""


class InvalidCredentialsError(Exception):
    """Email atau password tidak valid."""


class InactiveUserError(Exception):
    """Akun ditemukan tetapi tidak aktif."""


class InvalidRefreshTokenError(Exception):
    """Refresh token invalid, kedaluwarsa, atau sudah digunakan."""


class AccessDeniedError(Exception):
    """Pengguna tidak berwenang mengakses sumber daya yang diminta."""
