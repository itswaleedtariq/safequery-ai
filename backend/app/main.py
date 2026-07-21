from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import get_settings


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
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)