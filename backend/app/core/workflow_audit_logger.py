import hashlib
import json
import logging
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from backend.app.core.config import (
    PROJECT_ROOT,
    get_settings,
)


settings = get_settings()


@lru_cache(maxsize=1)
def get_workflow_logger() -> logging.Logger:
    """Create a rotating JSON-lines workflow logger."""

    log_path = Path(
        settings.workflow_log_file
    )

    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(
        "safequery.workflow"
    )

    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )

        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(message)s"
            )
        )

        logger.addHandler(handler)

    return logger


def log_query_workflow(
    *,
    request_id: str,
    question: str,
    status: str,
    confidence_score: float | None,
    row_count: int,
    total_latency_ms: float,
    warning_codes: list[str],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record one complete query workflow decision."""

    payload = {
        "request_id": request_id,
        "question_hash": hashlib.sha256(
            question.encode("utf-8")
        ).hexdigest(),
        "status": status,
        "confidence_score": confidence_score,
        "row_count": row_count,
        "total_latency_ms": total_latency_ms,
        "warning_codes": warning_codes,
        "metadata": metadata or {},
    }

    get_workflow_logger().info(
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )