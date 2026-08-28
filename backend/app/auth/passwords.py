import base64
import binascii
import hashlib
import hmac
import re
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
HASH_VERSION = "v1"
_USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


def normalize_username(value: str) -> str:
    normalized = value.strip().lower()
    if not _USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Username must be 3-64 characters using letters, numbers, dot, underscore, or hyphen."
        )
    return normalized


def validate_password(value: str) -> str:
    if len(value) < 12 or len(value) > 256:
        raise ValueError("Password must be between 12 and 256 characters.")
    return value


def hash_password(value: str, *, salt: bytes | None = None) -> str:
    password = validate_password(value).encode("utf-8")
    resolved_salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password,
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


def verify_password(value: str, encoded: str) -> bool:
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
            value.encode("utf-8"),
            salt=salt,
            n=parameters[0],
            r=parameters[1],
            p=parameters[2],
            dklen=len(expected),
        )
    except (binascii.Error, ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


DUMMY_PASSWORD_HASH = hash_password(
    "roadtalk-dummy-password-not-a-user",
    salt=b"roadtalk-auth-v1",
)
