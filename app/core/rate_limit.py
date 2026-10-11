"""Rate limit sederhana per proses sebagai lapisan proteksi awal.

Untuk deployment multi-worker/multi-instance, ganti state lokal ini dengan backend
bersama (misalnya Redis). Jangan mengandalkan limiter per proses sebagai satu-satunya
kontrol DoS pada production.
"""
from collections import OrderedDict
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

from app.core.config import settings

_WINDOW_SECONDS = settings.rate_limit_window_seconds
_MAX_KEYS = 10_000
_hits: OrderedDict[str, tuple[float, int]] = OrderedDict()
_lock = Lock()
_request_count = 0


def reset_rate_limit_state_for_tests() -> None:
    """Membersihkan state limiter untuk pengujian terisolasi."""
    global _request_count
    with _lock:
        _hits.clear()
        _request_count = 0


def rate_limit_dependency(*, scope: str, limit: int):
    async def check_rate_limit(request: Request) -> None:
        global _request_count
        client_host = request.client.host if request.client else "unknown"
        key = f"{scope}:{request.url.path}:{client_host}"
        now = monotonic()
        with _lock:
            record = _hits.get(key)
            if record is not None:
                started, count = record
                if now - started >= _WINDOW_SECONDS:
                    _hits[key] = (now, 1)
                elif count >= limit:
                    retry_after = max(1, int(_WINDOW_SECONDS - (now - started)))
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Terlalu banyak permintaan. Coba lagi nanti."},
                        headers={"Retry-After": str(retry_after)},
                    )
                else:
                    _hits[key] = (started, count + 1)
                _hits.move_to_end(key)
            else:
                if len(_hits) >= _MAX_KEYS:
                    # Pembersihan penuh hanya saat kapasitas state mendekati batas.
                    expired = [k for k, (started, _) in _hits.items() if now - started >= _WINDOW_SECONDS]
                    for expired_key in expired:
                        _hits.pop(expired_key, None)
                    while len(_hits) >= _MAX_KEYS:
                        _hits.popitem(last=False)
                _hits[key] = (now, 1)
            _request_count += 1
            # Prune kedaluwarsa secara periodik, bukan pada setiap request.
            if _request_count % 256 == 0:
                expired = [k for k, (started, _) in _hits.items() if now - started >= _WINDOW_SECONDS]
                for expired_key in expired:
                    _hits.pop(expired_key, None)

    return check_rate_limit


api_rate_limit = rate_limit_dependency(scope="api", limit=settings.api_rate_limit_requests)
auth_rate_limit = rate_limit_dependency(scope="auth", limit=settings.auth_rate_limit_requests)
ai_rate_limit = rate_limit_dependency(scope="ai", limit=settings.ai_rate_limit_requests)
