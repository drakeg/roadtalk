import base64
import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass

RECOVERY_KEY_PREFIX = "rtk1"
RECOVERY_SECRET_BYTES = 32
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
HASH_VERSION = "v1"


@dataclass(frozen=True, slots=True)
class RecoveryKey:
    raw: str
    key_id: uuid.UUID


class RecoveryKeyFormatError(ValueError):
    pass


def new_recovery_key() -> RecoveryKey:
    key_id = uuid.uuid4()
    secret = secrets.token_urlsafe(RECOVERY_SECRET_BYTES)
    return RecoveryKey(
        raw=f"{RECOVERY_KEY_PREFIX}.{key_id.hex}.{secret}",
        key_id=key_id,
    )


def parse_recovery_key(raw: str) -> tuple[uuid.UUID, bytes]:
    parts = raw.split(".")
    if len(parts) != 3 or parts[0] != RECOVERY_KEY_PREFIX:
        raise RecoveryKeyFormatError("Recovery key format is invalid.")
    try:
        key_id = uuid.UUID(hex=parts[1])
        padding = "=" * (-len(parts[2]) % 4)
        secret = base64.urlsafe_b64decode(parts[2] + padding)
    except (ValueError, TypeError) as exc:
        raise RecoveryKeyFormatError("Recovery key format is invalid.") from exc
    if len(secret) != RECOVERY_SECRET_BYTES:
        raise RecoveryKeyFormatError("Recovery key format is invalid.")
    return key_id, secret


def recovery_key_id(raw: str) -> uuid.UUID | None:
    try:
        key_id, _ = parse_recovery_key(raw)
    except RecoveryKeyFormatError:
        return None
    return key_id


def _password(raw: str, pepper: str) -> bytes:
    return hmac.new(
        pepper.encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha256,
    ).digest()


def hash_recovery_key(
    raw: str,
    pepper: str,
    *,
    salt: bytes | None = None,
) -> str:
    resolved_salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        _password(raw, pepper),
        salt=resolved_salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return "$".join(
        (
            "scrypt",
            HASH_VERSION,
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            base64.urlsafe_b64encode(resolved_salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_recovery_key(raw: str, encoded: str, pepper: str) -> bool:
    try:
        algorithm, version, n, r, p, salt_text, digest_text = encoded.split("$")
        if algorithm != "scrypt" or version != HASH_VERSION:
            return False
        parameters = (int(n), int(r), int(p))
        if parameters != (SCRYPT_N, SCRYPT_R, SCRYPT_P):
            return False
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(digest_text)
        actual = hashlib.scrypt(
            _password(raw, pepper),
            salt=salt,
            n=parameters[0],
            r=parameters[1],
            p=parameters[2],
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


DUMMY_RECOVERY_HASH = hash_recovery_key(
    "rtk1.00000000000000000000000000000000.invalid",
    "roadtalk-dummy-recovery-pepper",
    salt=b"roadtalk-dummy!!",
)
