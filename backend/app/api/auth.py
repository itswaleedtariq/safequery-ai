from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.app.api.dependencies import (
    CurrentUser,
)
from backend.app.core.exceptions import (
    AuthenticationConfigurationError,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from backend.app.db.app_session import (
    get_db_session,
)
from backend.app.schemas.auth import (
    AccessTokenResponse,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
)
from backend.app.services.auth_service import (
    authenticate_user,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/signup",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    request: UserSignupRequest,
    session: Annotated[
        Session,
        Depends(get_db_session),
    ],
) -> AccessTokenResponse:
    """Create a user account."""

    try:
        return register_user(
            session,
            request,
        )

    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except AuthenticationConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post(
    "/login",
    response_model=AccessTokenResponse,
)
def login(
    request: UserLoginRequest,
    session: Annotated[
        Session,
        Depends(get_db_session),
    ],
) -> AccessTokenResponse:
    """Authenticate a user and return a JWT."""

    try:
        return authenticate_user(
            session,
            request,
        )

    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error

    except InactiveUserError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except AuthenticationConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_account(
    current_user: CurrentUser,
) -> UserResponse:
    """Return the authenticated account."""

    return UserResponse.model_validate(
        current_user
    )