import json
import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.context import bind_request_id, reset_request_id
from app.logging import JsonFormatter, configure_logging
from app.main import create_app


def test_json_formatter_adds_context_and_safe_structured_fields() -> None:
    token = bind_request_id("request-123")
    try:
        record = logging.LogRecord(
            name="roadtalk.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="request.complete",
            args=(),
            exc_info=None,
        )
        record.status_code = 200
        payload = json.loads(JsonFormatter().format(record))
    finally:
        reset_request_id(token)

    assert payload["event"] == "request.complete"
    assert payload["request_id"] == "request-123"
    assert payload["status_code"] == 200
    assert "args" not in payload


def test_json_formatter_rejects_unapproved_events_and_sensitive_extras() -> None:
    record = logging.LogRecord(
        name="roadtalk.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="rtk1.synthetic-secret",
        args=(),
        exc_info=None,
    )
    record.recovery_key = "rtk1.synthetic-secret"
    record.callsign = "Synthetic-Callsign"
    record.latitude = 40.123456
    record.longitude = -75.654321
    record.horizontal_accuracy_m = 7.25
    record.heading_deg = 91.5
    record.speed_mps = 12.75
    record.source_device_id = "synthetic-source-device"
    record.route = "/api/v1/sessions/recover"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "log.event.rejected"
    assert payload["route"] == "/api/v1/sessions/recover"
    assert "recovery_key" not in payload
    assert "callsign" not in payload
    assert "rtk1.synthetic-secret" not in json.dumps(payload)
    assert "Synthetic-Callsign" not in json.dumps(payload)
    encoded = json.dumps(payload)
    for private_value in (
        "40.123456",
        "-75.654321",
        "7.25",
        "91.5",
        "12.75",
        "synthetic-source-device",
    ):
        assert private_value not in encoded


def test_request_logs_use_route_templates_not_concrete_identifiers(
    capsys: pytest.CaptureFixture[str],
) -> None:
    application = create_app(
        Settings(
            environment="test",
            database_check_enabled=False,
            log_level="INFO",
        )
    )
    device_id = str(uuid.uuid4())

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.delete(f"/api/v1/auth/devices/{device_id}")

    captured = capsys.readouterr()
    assert response.status_code == 401
    assert device_id not in captured.err
    assert "/api/v1/auth/devices/{device_id}" in captured.err
    assert '"problem_code":"AUTHENTICATION_REQUIRED"' in captured.err


def test_configure_logging_replaces_root_handlers() -> None:
    configure_logging("warning")

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
