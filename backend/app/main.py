from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.identity import router as identity_router
from app.api.recovery import router as recovery_router
from app.api.system import router as system_router
from app.config import Settings, get_settings
from app.db.session import check_database, dispose_database
from app.health import ReadinessRegistry
from app.identity.callsigns import CallsignAvailabilityLimiter
from app.logging import configure_logging
from app.middleware import RequestContextMiddleware
from app.problems import install_problem_handlers
from app.recovery.limiter import RecoveryLimiter


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await dispose_database()

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
    app.state.callsign_limiter = CallsignAvailabilityLimiter(
        limit=resolved.callsign_availability_limit,
        window_seconds=resolved.callsign_availability_window_seconds,
    )
    app.state.recovery_limiter = RecoveryLimiter(
        attempt_limit=resolved.recovery_attempt_limit,
        attempt_window_seconds=resolved.recovery_attempt_window_seconds,
        mutation_limit=resolved.recovery_mutation_limit,
        mutation_window_seconds=resolved.recovery_mutation_window_seconds,
    )
    if resolved.database_check_enabled:
        app.state.readiness.register("database", check_database)
    app.add_middleware(RequestContextMiddleware, settings=resolved)
    install_problem_handlers(app)
    app.include_router(system_router)
    app.include_router(auth_router)
    app.include_router(identity_router)
    app.include_router(recovery_router)
    return app


app = create_app()
