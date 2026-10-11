"""Middleware ASGI untuk membatasi ukuran body request secara aktual."""
import json


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        content_length = None
        for name, value in scope.get("headers", []):
            if name.lower() == b"content-length":
                try:
                    content_length = int(value.decode("ascii"))
                except (ValueError, UnicodeDecodeError):
                    await self._reject(send, 400, "INVALID_CONTENT_LENGTH", "Header Content-Length tidak valid.")
                    return
                break

        if content_length is not None and content_length > self.max_body_bytes:
            await self._reject(send, 413, "REQUEST_BODY_TOO_LARGE", "Ukuran body melebihi batas yang diizinkan.")
            return

        # Endpoint aplikasi memakai body JSON/form kecil, bukan streaming upload.
        # Buffer hanya sampai batas konfigurasi agar chunked body juga dibatasi.
        messages = []
        total = 0
        while True:
            message = await receive()
            if message.get("type") == "http.disconnect":
                return
            if message.get("type") != "http.request":
                messages.append(message)
                continue
            body_chunk = message.get("body", b"")
            total += len(body_chunk)
            if total > self.max_body_bytes:
                await self._reject(send, 413, "REQUEST_BODY_TOO_LARGE", "Ukuran body melebihi batas yang diizinkan.")
                return
            messages.append(message)
            if not message.get("more_body", False):
                break

        cursor = 0

        async def replay_receive():
            nonlocal cursor
            if cursor < len(messages):
                message = messages[cursor]
                cursor += 1
                return message
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _reject(send, status_code: int, code: str, message: str) -> None:
        body = json.dumps({"detail": {"code": code, "message": message}}).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"cache-control", b"no-store"),
            ],
        })
        await send({"type": "http.response.body", "body": body})
