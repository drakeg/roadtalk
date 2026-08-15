import pytest

from app.channels.limiter import ChannelInviteLimiter, ChannelRateLimitError
from app.channels.security import (
    DUMMY_INVITE_HASH,
    hash_invite,
    invite_fingerprint,
    new_invite,
    verify_invite,
)


def test_invite_is_high_entropy_slow_hashed_and_fingerprinted() -> None:
    invite = new_invite()
    encoded = hash_invite(invite, "pepper", salt=b"0123456789abcdef")

    assert invite.startswith("rtc1.")
    assert len(invite) >= 40
    assert invite not in encoded
    assert encoded.startswith("scrypt$v1$")
    assert len(invite_fingerprint(invite)) == 12
    assert verify_invite(invite, encoded, "pepper") is True
    assert verify_invite(f"{invite}x", encoded, "pepper") is False
    assert verify_invite(invite, encoded, "wrong") is False
    assert verify_invite("rtc1.invalid", DUMMY_INVITE_HASH, "") is True


def test_invite_limiter_covers_peer_and_account() -> None:
    limiter = ChannelInviteLimiter(limit=2, window_seconds=60)
    limiter.check(peer="peer-a", account_id="account-a", now=0)
    limiter.check(peer="peer-a", account_id="account-a", now=1)

    with pytest.raises(ChannelRateLimitError) as exc_info:
        limiter.check(peer="peer-a", account_id="account-a", now=2)

    assert exc_info.value.retry_after == 58
    limiter.check(peer="peer-a", account_id="account-a", now=61)
