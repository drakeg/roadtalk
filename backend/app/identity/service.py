import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.identity.avatars import AvatarSelectionError, validate_avatar_selection
from app.identity.callsigns import CallsignPolicyError, validate_callsign
from app.identity.schemas import (
    CallsignAvailabilityResponse,
    ProfileResponse,
    PublicIdentity,
)


class ProfileMutationError(ValueError):
    def __init__(
        self,
        code: str,
        detail: str,
        *,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.retry_after = retry_after


def profile_response(profile: Profile | None) -> ProfileResponse:
    return ProfileResponse(
        identity=PublicIdentity(
            callsign=profile.display_callsign if profile else None,
            avatar_id=profile.avatar_id if profile else None,
        ),
        setup_completed=profile.setup_completed if profile else False,
        version=profile.version if profile else 0,
    )


async def read_profile(db: AsyncSession, *, account_id: uuid.UUID) -> ProfileResponse:
    profile = await db.scalar(select(Profile).where(Profile.account_id == account_id))
    return profile_response(profile)


async def update_profile(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    candidate: str | None,
    expected_version: int,
    cooldown_seconds: int,
    avatar_id: str | None = None,
    now: datetime | None = None,
) -> ProfileResponse:
    callsign = None
    if candidate is not None:
        try:
            callsign = validate_callsign(candidate)
        except CallsignPolicyError as exc:
            raise ProfileMutationError(exc.code, exc.detail) from exc

    avatar = None
    if avatar_id is not None:
        try:
            avatar = validate_avatar_selection(avatar_id)
        except AvatarSelectionError as exc:
            raise ProfileMutationError("AVATAR_UNAVAILABLE", str(exc)) from exc

    if callsign is None and avatar is None:
        raise ProfileMutationError(
            "PROFILE_UPDATE_EMPTY",
            "At least one profile field must be supplied.",
        )

    changed_at = now or datetime.now(UTC).replace(tzinfo=None)
    profile = await db.scalar(
        select(Profile).where(Profile.account_id == account_id).with_for_update()
    )
    if profile is None:
        is_new = True
        if expected_version != 0:
            raise ProfileMutationError(
                "PROFILE_VERSION_CONFLICT",
                "The profile changed. Reload it before saving.",
            )
        profile = Profile(
            account_id=account_id,
            normalized_callsign=callsign.normalized if callsign else None,
            display_callsign=callsign.display if callsign else None,
            avatar_id=avatar.id if avatar else None,
            setup_completed=callsign is not None and avatar is not None,
            callsign_changed_at=changed_at if callsign else None,
        )
        db.add(profile)
    else:
        is_new = False
        if profile.version != expected_version:
            raise ProfileMutationError(
                "PROFILE_VERSION_CONFLICT",
                "The profile changed. Reload it before saving.",
            )
        normalized_changed = (
            callsign is not None and profile.normalized_callsign != callsign.normalized
        )
        if normalized_changed and profile.callsign_changed_at is not None:
            available_at = profile.callsign_changed_at + timedelta(seconds=cooldown_seconds)
            if available_at > changed_at:
                retry_after = max(1, int((available_at - changed_at).total_seconds()) + 1)
                raise ProfileMutationError(
                    "CALLSIGN_CHANGE_COOLDOWN",
                    "The callsign cannot be changed yet.",
                    retry_after=retry_after,
                )
        if callsign is not None:
            profile.normalized_callsign = callsign.normalized
            profile.display_callsign = callsign.display
        if avatar is not None:
            profile.avatar_id = avatar.id
        profile.setup_completed = (
            profile.normalized_callsign is not None and profile.avatar_id is not None
        )
        profile.version += 1
        if normalized_changed:
            profile.callsign_changed_at = changed_at

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if is_new:
            existing = await db.scalar(
                select(Profile.account_id).where(Profile.account_id == account_id)
            )
            if existing is not None:
                raise ProfileMutationError(
                    "PROFILE_VERSION_CONFLICT",
                    "The profile changed. Reload it before saving.",
                ) from exc
        raise ProfileMutationError(
            "CALLSIGN_UNAVAILABLE",
            "This callsign is unavailable.",
        ) from exc

    return profile_response(profile)


async def callsign_availability(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    candidate: str,
) -> CallsignAvailabilityResponse:
    try:
        callsign = validate_callsign(candidate)
    except CallsignPolicyError as exc:
        reason = "reserved" if exc.code == "CALLSIGN_RESERVED" else "invalid"
        return CallsignAvailabilityResponse(available=False, reason=reason)

    owner = await db.scalar(
        select(Profile.account_id).where(
            Profile.normalized_callsign == callsign.normalized,
            Profile.account_id != account_id,
        )
    )
    if owner is not None:
        return CallsignAvailabilityResponse(available=False, reason="taken")
    return CallsignAvailabilityResponse(available=True, reason="available")
