"""Validasi nilai masukan numerik dan sanitasi teks pengguna."""
import math
import unicodedata


def require_finite_number(value: object, *, field_name: str) -> float:
    """Validasi numeric input dan menolak NaN, infinity, bool, dan string."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} harus berupa angka.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} harus berupa angka finite.")
    return number


def sanitize_text(value: str, *, max_length: int, allow_empty: bool = False) -> str:
    """Normalisasi teks dan mengganti karakter kontrol dengan spasi.

    Ini mengurangi risiko control-character/log injection. Output HTML tetap harus
    di-escape pada client; sanitasi bukan pengganti output encoding.
    """
    normalized = unicodedata.normalize("NFKC", value)
    cleaned = "".join(
        " " if unicodedata.category(char) in {"Cc", "Cf"} else char
        for char in normalized
    )
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_length:
        raise ValueError(f"Teks tidak boleh melebihi {max_length} karakter setelah sanitasi.")
    if not allow_empty and not cleaned:
        raise ValueError("Teks tidak boleh kosong setelah sanitasi.")
    return cleaned
