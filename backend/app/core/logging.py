import json
import logging
from datetime import UTC, datetime
from typing import Any

_STANDARD_LOG_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)


class JsonFormatter(logging.Formatter):
    """Render application log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in _STANDARD_LOG_RECORD_FIELDS
            }
        )

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure JSON console logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        force=True,
    )

    formatter = JsonFormatter()
    for logger_name in (None, "uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            handler.setFormatter(formatter)
