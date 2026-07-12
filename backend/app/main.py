from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.system import router as system_router
from app.config import Settings, get_settings
from app.health import ReadinessRegistry
from app.logging import configure_logging
from app.middleware import RequestContextMiddleware
from app.problems import install_problem_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(
        title=resolved.app_name,
        version=resolved.version,
        docs_url="/docs" if resolved.docs_enabled else None,
        redoc_url="/redoc" if resolved.docs_enabled else None,
        openapi_url="/openapi.json" if resolved.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.readiness = ReadinessRegistry()
    app.add_middleware(RequestContextMiddleware, settings=resolved)
    install_problem_handlers(app)
    app.include_router(system_router)
    return app


app = create_app()
