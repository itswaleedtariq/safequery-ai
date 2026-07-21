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
def get_hallucination_logger() -> logging.Logger:
    """Create a rotating hallucination audit logger."""

    log_path = Path(
        settings.hallucination_log_file
    )

    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(
        "safequery.hallucination"
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


def log_hallucination_decision(
    *,
    question: str,
    sql: str,
    detected: bool,
    risk_level: str,
    alignment_score: float,
    schema_coverage_score: float,
    issue_codes: list[str],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record one hallucination-detection decision."""

    payload = {
        "question_hash": hashlib.sha256(
            question.encode("utf-8")
        ).hexdigest(),
        "sql_hash": hashlib.sha256(
            sql.encode("utf-8")
        ).hexdigest(),
        "detected": detected,
        "risk_level": risk_level,
        "alignment_score": alignment_score,
        "schema_coverage_score": (
            schema_coverage_score
        ),
        "issue_codes": issue_codes,
        "metadata": metadata or {},
    }

    get_hallucination_logger().info(
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )