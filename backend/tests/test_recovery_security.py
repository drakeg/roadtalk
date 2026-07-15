import uuid

from app.recovery.security import (
    RECOVERY_SECRET_BYTES,
    hash_recovery_key,
    new_recovery_key,
    parse_recovery_key,
    recovery_key_id,
    verify_recovery_key,
)


def test_recovery_key_has_version_selector_and_256_bit_secret() -> None:
    issued = new_recovery_key()
    key_id, secret = parse_recovery_key(issued.raw)

    assert issued.raw.startswith("rtk1.")
    assert key_id == issued.key_id
    assert len(secret) == RECOVERY_SECRET_BYTES
    assert recovery_key_id(issued.raw) == issued.key_id


def test_scrypt_hash_is_salted_versioned_and_peppered() -> None:
    issued = new_recovery_key()
    first = hash_recovery_key(
        issued.raw,
        "pepper-one",
        salt=b"0123456789abcdef",
    )
    second = hash_recovery_key(
        issued.raw,
        "pepper-one",
        salt=b"fedcba9876543210",
    )

    assert first.startswith("scrypt$v1$16384$8$1$")
    assert issued.raw not in first
    assert first != second
    assert verify_recovery_key(issued.raw, first, "pepper-one")
    assert not verify_recovery_key(issued.raw, first, "pepper-two")
    assert not verify_recovery_key(issued.raw + "x", first, "pepper-one")


def test_malformed_recovery_keys_fail_closed() -> None:
    for value in ("", "unknown", f"rtk1.{uuid.uuid4().hex}.short"):
        assert recovery_key_id(value) is None
