from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from fastapi import Request, status
from fastapi.responses import JSONResponse

from backend.app.core.exceptions import (
    AuthenticationConfigurationError,
    InactiveUserError,
    InvalidTokenError,
)

settings = get_settings()


def get_allowed_origins() -> list[str]:
    """Convert the configured comma-separated origins into a list."""

    return [
        origin.strip()
        for origin in settings.frontend_origins.split(",")
        if origin.strip()
    ]


app = FastAPI(
    title="SafeQuery AI",
    description=(
        "Secure Text-to-SQL analytics platform with "
        "guardrails, hallucination detection and "
        "confidence scoring."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.exception_handler(InvalidTokenError)
def handle_invalid_token(
    request: Request,
    error: InvalidTokenError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": str(error),
        },
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


@app.exception_handler(InactiveUserError)
def handle_inactive_user(
    request: Request,
    error: InactiveUserError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": str(error),
        },
    )


@app.exception_handler(
    AuthenticationConfigurationError
)
def handle_auth_configuration(
    request: Request,
    error: AuthenticationConfigurationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": str(error),
        },
    )