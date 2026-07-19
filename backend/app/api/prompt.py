import json
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from backend.app.schemas.prompt_context import (
    PromptPreviewRequest,
    PromptPreviewResponse,
)
from backend.app.services.prompt_builder import (
    build_prompt_preview,
)


router = APIRouter(tags=["Prompt Engine"])


@router.post(
    "/prompt/preview",
    response_model=PromptPreviewResponse,
    summary="Build a schema-aware Text-to-SQL prompt",
)
def preview_prompt(
    request: PromptPreviewRequest,
) -> PromptPreviewResponse:
    """
    Select relevant schema context and construct an LLM prompt.

    This endpoint does not call an LLM and does not execute SQL.
    """

    try:
        return build_prompt_preview(request)

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The database schema could not be loaded while "
                "constructing the prompt."
            ),
        ) from error

    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prompt configuration data could not be loaded.",
        ) from error