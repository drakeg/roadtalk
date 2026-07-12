import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.config import Settings


class AccessTokenError(ValueError):
    pass


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str, pepper: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"), token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def issue_access_token(
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    session_id: uuid.UUID,
    settings: Settings,
) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(account_id),
        "device_id": str(device_id),
        "session_id": str(session_id),
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl_seconds),
        "iss": settings.token_issuer,
        "aud": settings.token_audience,
    }
    return jwt.encode(
        claims,
        settings.token_signing_key.get_secret_value(),
        algorithm="HS256",
    )


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.token_signing_key.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.token_issuer,
            audience=settings.token_audience,
            options={"require": ["sub", "device_id", "session_id", "iat", "exp"]},
        )
    except InvalidTokenError as exc:
        raise AccessTokenError("Access token is invalid or expired.") from exc
