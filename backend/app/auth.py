"""Lightweight but real authentication.

PBKDF2 password hashing (stdlib, no extra deps) + opaque bearer tokens stored on
the user. Good enough for a hackathon MVP; swap for OAuth/SSO in production.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        _, iters, salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)
