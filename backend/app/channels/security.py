import base64
import hashlib
import hmac
import secrets

INVITE_PREFIX = "rtc1"
INVITE_SECRET_BYTES = 32
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def new_invite() -> str:
    return f"{INVITE_PREFIX}.{secrets.token_urlsafe(INVITE_SECRET_BYTES)}"


def invite_fingerprint(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def hash_invite(raw: str, pepper: str, *, salt: bytes | None = None) -> str:
    resolved_salt = salt or secrets.token_bytes(16)
    password = hmac.new(pepper.encode(), raw.encode(), hashlib.sha256).digest()
    digest = hashlib.scrypt(password, salt=resolved_salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return "$".join(
        (
            "scrypt",
            "v1",
            base64.urlsafe_b64encode(resolved_salt).decode(),
            base64.urlsafe_b64encode(digest).decode(),
        )
    )


def verify_invite(raw: str, encoded: str, pepper: str) -> bool:
    try:
        algorithm, version, salt_text, expected_text = encoded.split("$")
        if (algorithm, version) != ("scrypt", "v1"):
            return False
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(expected_text)
        password = hmac.new(pepper.encode(), raw.encode(), hashlib.sha256).digest()
        actual = hashlib.scrypt(password, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


DUMMY_INVITE_HASH = hash_invite(
    "rtc1.invalid",
    "",
    salt=b"roadtalk-invite!",
)
