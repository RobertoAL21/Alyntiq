import json
import logging

from app.core.logging import JsonFormatter, configure_logging


def test_json_formatter_emits_structured_log_record() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="alyntiq.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="service started",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "alyntiq.test"
    assert payload["message"] == "service started"
    assert payload["timestamp"].endswith("+00:00")


def test_configure_logging_uses_json_for_root_handlers() -> None:
    configure_logging()

    root_handlers = logging.getLogger().handlers

    assert all(isinstance(handler.formatter, JsonFormatter) for handler in root_handlers)
