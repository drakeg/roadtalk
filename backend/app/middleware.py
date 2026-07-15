import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import Settings
from app.context import bind_request_id, reset_request_id

logger = logging.getLogger("roadtalk.request")


def route_template(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path_format", None) or getattr(route, "path", None)
    return template if isinstance(template, str) else "unmatched"


def result_class(status_code: int) -> str:
    if status_code < 400:
        return "success"
    if status_code < 500:
        return "client_error"
    return "server_error"


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        supplied = request.headers.get("X-Request-ID", "").strip()
        request_id = (
            supplied
            if supplied and len(supplied) <= self.settings.trusted_request_id_max_length
            else str(uuid4())
        )
        request.state.request_id = request_id
        token = bind_request_id(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request.complete",
                extra={
                    "method": request.method,
                    "route": route_template(request),
                    "status_code": response.status_code,
                    "result_class": result_class(response.status_code),
                    "duration_ms": duration_ms,
                },
            )
            return response
        finally:
            reset_request_id(token)
