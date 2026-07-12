import json
import logging

from app.context import bind_request_id, reset_request_id
from app.logging import JsonFormatter, configure_logging


def test_json_formatter_adds_context_and_safe_structured_fields() -> None:
    token = bind_request_id("request-123")
    try:
        record = logging.LogRecord(
            name="roadtalk.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="test.event",
            args=(),
            exc_info=None,
        )
        record.status_code = 200
        payload = json.loads(JsonFormatter().format(record))
    finally:
        reset_request_id(token)

    assert payload["event"] == "test.event"
    assert payload["request_id"] == "request-123"
    assert payload["status_code"] == 200
    assert "args" not in payload


def test_configure_logging_replaces_root_handlers() -> None:
    configure_logging("warning")

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
