import hashlib
from collections import deque
from math import ceil


class PremiumRateLimitError(ValueError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Premium request is temporarily unavailable.")
        self.retry_after = retry_after


class PremiumStatusLimiter:
    """Bound Premium status reads by account, device, and network peer."""

    def __init__(
        self,
        *,
        account_limit: int,
        device_limit: int,
        peer_limit: int,
        window_seconds: int,
        max_buckets: int = 20_000,
    ) -> None:
        self.account_limit = account_limit
        self.device_limit = device_limit
        self.peer_limit = peer_limit
        self.window_seconds = window_seconds
        self.max_buckets = max_buckets
        self._events: dict[tuple[str, str], deque[float]] = {}

    def check(
        self,
        *,
        peer: str,
        account_id: str,
        device_id: str,
        now: float,
    ) -> None:
        dimensions = (
            (("premium-account", account_id), self.account_limit),
            (("premium-device", device_id), self.device_limit),
            (("premium-peer", hashlib.sha256(peer.encode("utf-8")).hexdigest()), self.peer_limit),
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
            raise PremiumRateLimitError(retry_after)
        for events in resolved:
            events.append(now)
