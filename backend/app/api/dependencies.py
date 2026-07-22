from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    InactiveUserError,
    InvalidTokenError,
)
from backend.app.core.security import (
    decode_access_token,
)
from backend.app.db.app_session import (
    get_db_session,
)
from backend.app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/v1/auth/login"
)


def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    session: Annotated[
        Session,
        Depends(get_db_session),
    ],
) -> User:
    """Return the authenticated active user."""

    user_id = decode_access_token(token)

    user = session.get(User, user_id)

    if user is None:
        raise InvalidTokenError(
            "The token user no longer exists."
        )

    if not user.is_active:
        raise InactiveUserError(
            "This account is inactive."
        )

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]