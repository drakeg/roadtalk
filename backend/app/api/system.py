from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Account, Channel, ChannelMembership, CurrentLocation, MediaGrant
from app.db.session import get_session

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


class ClientConfigResponse(BaseModel):
    location_policy_version: str
    location_disclosure_version: str
    media_provider_enabled: bool


class OperationalMetricsResponse(BaseModel):
    active_accounts: int
    active_locations: int
    enabled_channels: int
    active_memberships: int
    valid_media_grants: int


@router.get("/health/live", response_model=StatusResponse, include_in_schema=False)
async def live() -> StatusResponse:
    return StatusResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse, include_in_schema=False)
async def ready(request: Request) -> ReadinessResponse:
    checks = await request.app.state.readiness.evaluate()
    status = "ready" if all(value == "ready" for value in checks.values()) else "not_ready"
    return ReadinessResponse(status=status, checks=checks)


@router.get("/api/v1/system/version", response_model=VersionResponse)
async def version(request: Request) -> VersionResponse:
    settings: Settings = request.app.state.settings
    return VersionResponse(
        name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )


@router.get("/api/v1/system/client-config", response_model=ClientConfigResponse)
async def client_config(request: Request) -> ClientConfigResponse:
    settings: Settings = request.app.state.settings
    return ClientConfigResponse(
        location_policy_version=settings.location_policy_version,
        location_disclosure_version=settings.location_disclosure_version,
        media_provider_enabled=settings.ptt_media_provider_enabled,
    )


@router.get("/api/v1/system/metrics", response_model=OperationalMetricsResponse)
async def operational_metrics(
    session: AsyncSession = Depends(get_session),
) -> OperationalMetricsResponse:
    now = datetime.now(UTC)
    statements = (
        select(func.count()).select_from(Account).where(Account.status == "active"),
        select(func.count()).select_from(CurrentLocation).where(CurrentLocation.expires_at > now),
        select(func.count()).select_from(Channel).where(Channel.enabled.is_(True)),
        select(func.count())
        .select_from(ChannelMembership)
        .where(ChannelMembership.state == "active"),
        select(func.count())
        .select_from(MediaGrant)
        .where(MediaGrant.revoked_at.is_(None), MediaGrant.expires_at > now),
    )
    counts = [int((await session.execute(statement)).scalar_one()) for statement in statements]
    return OperationalMetricsResponse(
        active_accounts=counts[0],
        active_locations=counts[1],
        enabled_channels=counts[2],
        active_memberships=counts[3],
        valid_media_grants=counts[4],
    )
