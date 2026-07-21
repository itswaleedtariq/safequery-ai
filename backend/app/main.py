from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import get_settings


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Secure natural-language-to-SQL analytics platform with "
        "guardrails and hallucination detection."
    ),
    version="0.9.0",
)


app.include_router(api_router)