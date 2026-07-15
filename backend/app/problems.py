import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.context import request_id_context
from app.middleware import route_template

logger = logging.getLogger("roadtalk.error")


def log_problem(request: Request, *, status: int, code: str) -> None:
    logger.warning(
        "request.problem",
        extra={
            "method": request.method,
            "route": route_template(request),
            "status_code": status,
            "problem_code": code,
        },
    )


def problem(
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "type": f"https://roadtalk.example/problems/{code.lower().replace('_', '-')}",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail,
        "request_id": request_id_context.get(),
        "errors": errors or [],
    }


def install_problem_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        log_problem(request, status=422, code="VALIDATION_ERROR")
        errors = [
            {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=problem(
                status=422,
                code="VALIDATION_ERROR",
                title="Request validation failed",
                detail="One or more request fields are invalid.",
                errors=errors,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "HTTP_ERROR"
        detail = str(exc.detail)
        if isinstance(exc.detail, dict):
            code = str(exc.detail.get("code", code))
            detail = str(exc.detail.get("detail", "The request could not be completed."))
        log_problem(request, status=exc.status_code, code=code)
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content=problem(
                status=exc.status_code,
                code=code,
                title="Request failed",
                detail=detail,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "request.unhandled",
            extra={
                "method": request.method,
                "route": route_template(request),
                "status_code": 500,
                "problem_code": "INTERNAL_ERROR",
            },
        )
        request_id = str(getattr(request.state, "request_id", "unknown"))
        content = problem(
            status=500,
            code="INTERNAL_ERROR",
            title="Internal server error",
            detail="The request could not be completed.",
        )
        content["request_id"] = request_id
        return JSONResponse(
            status_code=500,
            headers={"X-Request-ID": request_id},
            content=content,
        )
