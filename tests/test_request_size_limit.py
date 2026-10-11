"""Test middleware membatasi body aktual, termasuk body chunked."""
import asyncio

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.request_size_limit import RequestBodyLimitMiddleware


def test_request_body_over_limit_returns_413():
    test_app = FastAPI()
    test_app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=16)

    @test_app.post("/echo")
    async def echo(request: Request):
        return {"size": len(await request.body())}

    response = TestClient(test_app).post("/echo", content=b"x" * 17)
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "REQUEST_BODY_TOO_LARGE"


def test_request_body_middleware_rejects_chunked_body_over_limit():
    async def endpoint_app(scope, receive, send):
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = RequestBodyLimitMiddleware(endpoint_app, max_body_bytes=5)
    sent = []
    chunks = [
        {"type": "http.request", "body": b"123", "more_body": True},
        {"type": "http.request", "body": b"456", "more_body": False},
    ]

    async def receive():
        return chunks.pop(0)

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "method": "POST", "path": "/test", "headers": []}
    asyncio.run(middleware(scope, receive, send))
    assert sent[0]["status"] == 413
