import hashlib
from collections import deque
from math import ceil


class ModerationRateLimitError(ValueError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Moderation request is temporarily unavailable.")
        self.retry_after = retry_after


class ModerationReportLimiter:
    """Bound report/replay attempts for the local single-worker evidence design."""

    def __init__(
        self,
        *,
        account_limit: int,
        device_limit: int,
        peer_limit: int,
        event_limit: int,
        window_seconds: int,
        max_buckets: int = 20_000,
    ) -> None:
        self.account_limit = account_limit
        self.device_limit = device_limit
        self.peer_limit = peer_limit
        self.event_limit = event_limit
        self.window_seconds = window_seconds
        self.max_buckets = max_buckets
        self._events: dict[tuple[str, str], deque[float]] = {}

    def check(
        self,
        *,
        peer: str,
        account_id: str,
        device_id: str,
        event_key: str,
        now: float,
    ) -> None:
        event_hash = hashlib.sha256(event_key.encode("utf-8")).hexdigest()
        dimensions = (
            (("moderation-account", account_id), self.account_limit),
            (("moderation-device", device_id), self.device_limit),
            (("moderation-peer", peer), self.peer_limit),
            (("moderation-event", f"{account_id}:{event_hash}"), self.event_limit),
        )
        cutoff = now - self.window_seconds
        retry_after = 0
        resolved: list[deque[float]] = []
        for key, limit in dimensions:
            events = self._events.get(key)
            if events is None:
                if len(self._events) >= self.max_buckets:
                    self._events.pop(next(iter(self._events)))
                events = deque()
                self._events[key] = events
            while events and events[0] <= cutoff:
                events.popleft()
            resolved.append(events)
            if len(events) >= limit:
                retry_after = max(
                    retry_after,
                    max(1, ceil(events[0] + self.window_seconds - now)),
                )
        if retry_after:
            raise ModerationRateLimitError(retry_after)
        for events in resolved:
            events.append(now)
