from collections import deque
from math import ceil


class PttRateLimitError(ValueError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("PTT grant requests are temporarily limited.")
        self.retry_after = retry_after


class PttLimiter:
    def __init__(
        self,
        *,
        receive_limit: int,
        receive_window_seconds: int,
        max_buckets: int = 20_000,
    ) -> None:
        self.receive_limit = receive_limit
        self.receive_window_seconds = receive_window_seconds
        self.max_buckets = max_buckets
        self._events: dict[tuple[str, str], deque[float]] = {}

    def check_receive(
        self,
        *,
        peer: str,
        account_id: str,
        device_id: str,
        now: float,
    ) -> None:
        self._check_many(
            (
                ("receive-peer", peer),
                ("receive-account", account_id),
                ("receive-device", device_id),
            ),
            limit=self.receive_limit,
            window_seconds=self.receive_window_seconds,
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
            raise PttRateLimitError(retry_after)
        for events in resolved:
            events.append(now)
