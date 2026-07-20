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
def get_query_audit_logger() -> logging.Logger:
    """Create a rotating JSON-lines execution logger."""

    log_path = Path(
        settings.query_audit_log_file
    )

    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(
        "safequery.execution"
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


def log_query_execution(
    *,
    sql: str,
    status: str,
    rows_returned: int = 0,
    execution_time_ms: float = 0.0,
    estimated_rows_scanned: int = 0,
    total_cost: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record one query execution decision."""

    normalized_preview = " ".join(
        sql.split()
    )[:500]

    payload = {
        "query_hash": hashlib.sha256(
            sql.encode("utf-8")
        ).hexdigest(),
        "status": status,
        "query_preview": normalized_preview,
        "rows_returned": rows_returned,
        "execution_time_ms": execution_time_ms,
        "estimated_rows_scanned": (
            estimated_rows_scanned
        ),
        "total_cost": total_cost,
        "metadata": metadata or {},
    }

    get_query_audit_logger().info(
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )