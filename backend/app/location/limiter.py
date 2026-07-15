from collections import deque
from math import ceil


class LocationRateLimitError(ValueError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Location requests are temporarily limited.")
        self.retry_after = retry_after


class LocationLimiter:
    def __init__(
        self,
        *,
        mutation_limit: int,
        mutation_window_seconds: int,
        nearby_read_limit: int,
        nearby_read_window_seconds: int,
        max_buckets: int = 20_000,
    ) -> None:
        self.mutation_limit = mutation_limit
        self.mutation_window_seconds = mutation_window_seconds
        self.nearby_read_limit = nearby_read_limit
        self.nearby_read_window_seconds = nearby_read_window_seconds
        self.max_buckets = max_buckets
        self._events: dict[tuple[str, str], deque[float]] = {}

    def check_mutation(
        self,
        *,
        peer: str,
        account_id: str,
        device_id: str,
        now: float,
    ) -> None:
        self._check_many(
            (
                ("mutation-peer", peer),
                ("mutation-account", account_id),
                ("mutation-device", device_id),
            ),
            limit=self.mutation_limit,
            window_seconds=self.mutation_window_seconds,
            now=now,
        )

    def check_nearby_read(
        self,
        *,
        peer: str,
        account_id: str,
        device_id: str,
        now: float,
    ) -> None:
        self._check_many(
            (
                ("nearby-peer", peer),
                ("nearby-account", account_id),
                ("nearby-device", device_id),
            ),
            limit=self.nearby_read_limit,
            window_seconds=self.nearby_read_window_seconds,
            now=now,
        )

    def _check_many(
        self,
        keys: tuple[tuple[str, str], ...],
        *,
        limit: int,
        window_seconds: int,
        now: float,
    ) -> None:
        retry_after = 0
        resolved: list[deque[float]] = []
        cutoff = now - window_seconds
        for key in keys:
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
                    max(1, ceil(events[0] + window_seconds - now)),
                )
        if retry_after:
            raise LocationRateLimitError(retry_after)
        for events in resolved:
            events.append(now)
