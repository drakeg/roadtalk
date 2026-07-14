from collections import deque
from math import ceil


class RecoveryRateLimitError(ValueError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Recovery requests are temporarily limited.")
        self.retry_after = retry_after


class RecoveryLimiter:
    def __init__(
        self,
        *,
        attempt_limit: int,
        attempt_window_seconds: int,
        mutation_limit: int,
        mutation_window_seconds: int,
        max_buckets: int = 20_000,
    ) -> None:
        self.attempt_limit = attempt_limit
        self.attempt_window_seconds = attempt_window_seconds
        self.mutation_limit = mutation_limit
        self.mutation_window_seconds = mutation_window_seconds
        self.max_buckets = max_buckets
        self._events: dict[tuple[str, str], deque[float]] = {}

    def check_attempt(
        self,
        *,
        peer: str,
        installation_id: str,
        selector: str,
        now: float,
    ) -> None:
        self._check_many(
            (
                ("attempt-peer", peer),
                ("attempt-device", installation_id),
                ("attempt-selector", selector),
            ),
            limit=self.attempt_limit,
            window_seconds=self.attempt_window_seconds,
            now=now,
        )

    def check_mutation(
        self,
        *,
        account_id: str,
        device_id: str,
        now: float,
    ) -> None:
        self._check_many(
            (
                ("mutation-account", account_id),
                ("mutation-device", device_id),
            ),
            limit=self.mutation_limit,
            window_seconds=self.mutation_window_seconds,
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
            raise RecoveryRateLimitError(retry_after)
        for events in resolved:
            events.append(now)
