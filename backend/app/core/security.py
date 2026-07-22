from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    AuthenticationConfigurationError,
    InvalidTokenError,
)


settings = get_settings()

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create a secure password hash."""

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    stored_hash: str,
) -> bool:
    """Verify a password against its stored hash."""

    return password_hash.verify(
        plain_password,
        stored_hash,
    )


def create_access_token(
    *,
    user_id: UUID,
    email: str,
) -> tuple[str, int]:
    """Create a signed JWT access token."""

    secret_key = settings.jwt_secret_key.strip()

    if not secret_key:
        raise AuthenticationConfigurationError(
            "JWT_SECRET_KEY is missing."
        )

    expires_in_seconds = (
        settings.jwt_access_token_minutes * 60
    )

    expires_at = datetime.now(UTC) + timedelta(
        seconds=expires_in_seconds
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": datetime.now(UTC),
        "exp": expires_at,
        "type": "access",
    }

    token = jwt.encode(
        payload,
        secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token, expires_in_seconds


def decode_access_token(token: str) -> UUID:
    """Validate a JWT and return its user ID."""

    secret_key = settings.jwt_secret_key.strip()

    if not secret_key:
        raise AuthenticationConfigurationError(
            "JWT_SECRET_KEY is missing."
        )

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.jwt_algorithm],
        )

    except jwt.ExpiredSignatureError as error:
        raise InvalidTokenError(
            "The access token has expired."
        ) from error

    except jwt.InvalidTokenError as error:
        raise InvalidTokenError(
            "The access token is invalid."
        ) from error

    if payload.get("type") != "access":
        raise InvalidTokenError(
            "The supplied token is not an access token."
        )

    subject = payload.get("sub")

    if not isinstance(subject, str):
        raise InvalidTokenError(
            "The access token does not contain a user ID."
        )

    try:
        return UUID(subject)

    except ValueError as error:
        raise InvalidTokenError(
            "The token user ID is invalid."
        ) from error