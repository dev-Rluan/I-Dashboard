import base64
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class BasicAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, username: str, password: str):
        super().__init__(app)
        self._cred = base64.b64encode(f"{username}:{password}".encode()).decode()

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path == "/api/system/health" or path.startswith("/api/agents"):
            return await call_next(request)
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Basic ") and auth[6:] == self._cred:
            return await call_next(request)
        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="I-Dashboard"'},
        )
