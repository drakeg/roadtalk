import re
import unicodedata
import uuid
from collections import deque
from dataclasses import dataclass
from math import ceil

MIN_CALLSIGN_LENGTH = 3
MAX_CALLSIGN_LENGTH = 24
CALLSIGN_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
RESERVED_CALLSIGNS = frozenset(
    {
        "admin",
        "anonymous",
        "emergency",
        "fire",
        "moderator",
        "official",
        "police",
        "roadtalk",
        "sheriff",
        "staff",
        "support",
        "system",
        "unavailable",
    }
)
RESERVED_PREFIXES = (
    "admin-",
    "emergency-",
    "moderator-",
    "official-",
    "roadtalk-",
    "staff-",
    "support-",
    "system-",
)


class CallsignPolicyError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class CallsignRateLimitError(ValueError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Callsign availability checks are temporarily limited.")
        self.retry_after = retry_after


@dataclass(frozen=True)
class Callsign:
    display: str
    normalized: str


def validate_callsign(value: str) -> Callsign:
    display = unicodedata.normalize("NFKC", value).strip()
    normalized = display.casefold()

    if not MIN_CALLSIGN_LENGTH <= len(normalized) <= MAX_CALLSIGN_LENGTH:
        raise CallsignPolicyError(
            "CALLSIGN_INVALID_LENGTH",
            f"Callsign must contain {MIN_CALLSIGN_LENGTH} to {MAX_CALLSIGN_LENGTH} characters.",
        )
    if not normalized.isascii() or not CALLSIGN_PATTERN.fullmatch(normalized):
        raise CallsignPolicyError(
            "CALLSIGN_INVALID_CHARACTERS",
            "Callsign may contain ASCII letters, numbers, and single hyphens, "
            "and must begin and end with a letter or number.",
        )
    if "--" in normalized:
        raise CallsignPolicyError(
            "CALLSIGN_INVALID_CHARACTERS",
            "Callsign may not contain consecutive hyphens.",
        )
    if normalized in RESERVED_CALLSIGNS or normalized.startswith(RESERVED_PREFIXES):
        raise CallsignPolicyError(
            "CALLSIGN_RESERVED",
            "This callsign is reserved.",
        )
    return Callsign(display=display, normalized=normalized)


class CallsignAvailabilityLimiter:
    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int,
        max_buckets: int = 10_000,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_buckets = max_buckets
        self._events: dict[tuple[uuid.UUID, uuid.UUID], deque[float]] = {}

    def check(
        self,
        *,
        account_id: uuid.UUID,
        device_id: uuid.UUID,
        now: float,
    ) -> None:
        key = (account_id, device_id)
        cutoff = now - self.window_seconds
        events = self._events.get(key)
        if events is None:
            if len(self._events) >= self.max_buckets:
                self._events.pop(next(iter(self._events)))
            events = deque()
            self._events[key] = events
        while events and events[0] <= cutoff:
            events.popleft()

        if len(events) >= self.limit:
            retry_after = max(1, ceil(events[0] + self.window_seconds - now))
            raise CallsignRateLimitError(retry_after)

        events.append(now)
