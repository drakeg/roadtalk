import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.context import request_id_context


class JsonFormatter(logging.Formatter):
    _allowed_events = {
        "request.complete",
        "request.problem",
        "request.unhandled",
    }
    _allowed_fields = {
        "duration_ms",
        "method",
        "problem_code",
        "result_class",
        "route",
        "status_code",
    }

    def format(self, record: logging.LogRecord) -> str:
        event = record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": event if event in self._allowed_events else "log.event.rejected",
        }
        request_id = request_id_context.get()
        if request_id:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key in self._allowed_fields:
                payload[key] = value

        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None

        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
