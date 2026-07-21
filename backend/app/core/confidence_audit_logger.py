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
def get_confidence_logger() -> logging.Logger:
    """Create a rotating confidence audit logger."""

    log_path = Path(
        settings.confidence_log_file
    )

    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(
        "safequery.confidence"
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


def log_confidence_decision(
    *,
    question: str,
    sql: str,
    score: float,
    label: str,
    signal_scores: dict[str, float | None],
    agreement_status: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record one confidence calculation."""

    payload = {
        "question_hash": hashlib.sha256(
            question.encode("utf-8")
        ).hexdigest(),
        "sql_hash": hashlib.sha256(
            sql.encode("utf-8")
        ).hexdigest(),
        "confidence_score": score,
        "confidence_label": label,
        "signal_scores": signal_scores,
        "agreement_status": agreement_status,
        "metadata": metadata or {},
    }

    get_confidence_logger().info(
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )