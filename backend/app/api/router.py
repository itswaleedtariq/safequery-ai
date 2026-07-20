from fastapi import APIRouter

from backend.app.api import health
from backend.app.api import prompt as prompt_routes
from backend.app.api import schema as schema_routes
from backend.app.api import (
    sql_generation as sql_generation_routes,
)


api_router = APIRouter()

api_router.include_router(health.router)

api_router.include_router(
    schema_routes.router,
    prefix="/v1",
)

api_router.include_router(
    prompt_routes.router,
    prefix="/v1",
)

api_router.include_router(
    sql_generation_routes.router,
    prefix="/v1",
)