from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter(tags=["system"])


class StatusResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


class VersionResponse(BaseModel):
    name: str
    version: str
    environment: str


@router.get("/health/live", response_model=StatusResponse, include_in_schema=False)
async def live() -> StatusResponse:
    return StatusResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse, include_in_schema=False)
async def ready(request: Request) -> ReadinessResponse:
    checks = await request.app.state.readiness.evaluate()
    status = "ready" if all(value == "ready" for value in checks.values()) else "not_ready"
    return ReadinessResponse(status=status, checks=checks)


@router.get("/api/v1/system/version", response_model=VersionResponse)
async def version(
    settings: Annotated[Settings, Depends(get_settings)],
) -> VersionResponse:
    return VersionResponse(
        name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )
