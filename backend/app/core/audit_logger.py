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
def get_guardrail_logger() -> logging.Logger:
    """Create a rotating JSON-lines guardrail logger."""

    log_path = Path(settings.guardrail_log_file)

    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(
        "safequery.guardrails"
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


def log_guardrail_decision(
    *,
    sql: str,
    allowed: bool,
    issue_codes: list[str],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write one guardrail decision to the audit log."""

    normalized_preview = " ".join(
        sql.split()
    )[:500]

    payload = {
        "query_hash": hashlib.sha256(
            sql.encode("utf-8")
        ).hexdigest(),
        "allowed": allowed,
        "issue_codes": issue_codes,
        "query_preview": normalized_preview,
        "metadata": metadata or {},
    }

    get_guardrail_logger().info(
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )