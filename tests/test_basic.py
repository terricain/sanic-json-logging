import json
import pytest

from sanic_json_logging.formatters import JSONFormatter, JSONReqFormatter


@pytest.mark.asyncio
async def test_json_access_logging(generic_app, logs):
    """
    GET request
    """
    with logs("sanic.access") as caplog:
        _, resp = await generic_app.asgi_client.get("/test_get")
        assert resp.status == 200

        # We should get no access logging
        for log_record in caplog.records:
            if log_record.name == "sanic.access":
                # Check log record has data passed from access logging middleware
                assert hasattr(log_record, "request")
                assert hasattr(log_record, "response")
                assert hasattr(log_record, "time")
                assert hasattr(log_record, "req_id")
                assert log_record.time != -1
                assert log_record.req_id != "unknown"


@pytest.mark.asyncio
async def test_json_custom_class_logging(custom_log_app, logs):
    """
    GET request
    """
    formatter = JSONFormatter()
    access_formatter = JSONReqFormatter()

    with logs("sanic.access") as caplog:
        _, resp = await custom_log_app.asgi_client.get("/test_get")
        assert resp.status == 200

        access_req_id = None
        log_req_id = None

        for log_record in caplog.records:
            if log_record.name == "sanic.access":
                rec = access_formatter.format(log_record)
                rec = json.loads(rec)

                access_req_id = rec['req_id']

            else:
                rec = formatter.format(log_record)
                rec = json.loads(rec)
                assert rec["message"] == "my class"

                log_req_id = rec['req_id']

        assert access_req_id is not None
        assert log_req_id == access_req_id
