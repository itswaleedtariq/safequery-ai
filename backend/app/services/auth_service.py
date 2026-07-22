from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
)
from backend.app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.app.models.user import User
from backend.app.schemas.auth import (
    AccessTokenResponse,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
)


def normalize_email(email: str) -> str:
    """Normalize an email before storage and comparison."""

    return email.strip().lower()


def find_user_by_email(
    session: Session,
    email: str,
) -> User | None:
    """Find a user using a case-insensitive email lookup."""

    normalized_email = normalize_email(email)

    statement = select(User).where(
        func.lower(User.email) == normalized_email
    )

    return session.scalar(statement)


def register_user(
    session: Session,
    request: UserSignupRequest,
) -> AccessTokenResponse:
    """Create a user and return an access token."""

    normalized_email = normalize_email(
        str(request.email)
    )

    existing_user = find_user_by_email(
        session,
        normalized_email,
    )

    if existing_user is not None:
        raise EmailAlreadyRegisteredError(
            "An account already exists for this email."
        )

    user = User(
        name=request.name.strip(),
        email=normalized_email,
        password_hash=hash_password(
            request.password
        ),
    )

    session.add(user)

    try:
        session.commit()

    except Exception:
        session.rollback()
        raise

    session.refresh(user)

    access_token, expires_in = (
        create_access_token(
            user_id=user.id,
            email=user.email,
        )
    )

    return AccessTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


def authenticate_user(
    session: Session,
    request: UserLoginRequest,
) -> AccessTokenResponse:
    """Validate credentials and issue an access token."""

    user = find_user_by_email(
        session,
        str(request.email),
    )

    if (
        user is None
        or not verify_password(
            request.password,
            user.password_hash,
        )
    ):
        raise InvalidCredentialsError(
            "Email or password is incorrect."
        )

    if not user.is_active:
        raise InactiveUserError(
            "This account is inactive."
        )

    access_token, expires_in = (
        create_access_token(
            user_id=user.id,
            email=user.email,
        )
    )

    return AccessTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )