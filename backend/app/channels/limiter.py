from collections import deque
from math import ceil


class ChannelRateLimitError(ValueError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Channel invite requests are temporarily limited.")
        self.retry_after = retry_after


class ChannelInviteLimiter:
    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[tuple[str, str], deque[float]] = {}

    def check(self, *, peer: str, account_id: str, now: float) -> None:
        cutoff = now - self.window_seconds
        buckets = []
        retry_after = 0
        for key in (("peer", peer), ("account", account_id)):
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            buckets.append(events)
            if len(events) >= self.limit:
                retry_after = max(retry_after, max(1, ceil(events[0] + self.window_seconds - now)))
        if retry_after:
            raise ChannelRateLimitError(retry_after)
        for events in buckets:
            events.append(now)
