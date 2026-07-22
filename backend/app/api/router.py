from fastapi import APIRouter

from backend.app.api import (
    confidence as confidence_routes,
)
from backend.app.api import (
    guardrails as guardrail_routes,
)
from backend.app.api import (
    hallucination as hallucination_routes,
)
from backend.app.api import health
from backend.app.api import prompt as prompt_routes
from backend.app.api import (
    query_execution as execution_routes,
)
from backend.app.api import (
    query_workflow as workflow_routes,
)
from backend.app.api import schema as schema_routes
from backend.app.api import (
    sql_generation as sql_generation_routes,
)

from backend.app.api import auth as auth_routes

api_router = APIRouter()

api_router.include_router(
    health.router
)

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

api_router.include_router(
    guardrail_routes.router,
    prefix="/v1",
)

api_router.include_router(
    execution_routes.router,
    prefix="/v1",
)

api_router.include_router(
    hallucination_routes.router,
    prefix="/v1",
)

api_router.include_router(
    confidence_routes.router,
    prefix="/v1",
)

api_router.include_router(
    workflow_routes.router,
    prefix="/v1",
)

api_router.include_router(
    auth_routes.router,
    prefix="/v1",
)