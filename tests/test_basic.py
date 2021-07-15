import json

from sanic_json_logging.formatters import JSONFormatter, JSONReqFormatter


async def test_json_access_logging(test_cli, logs):
    """
    GET request
    """
    with logs("sanic.access") as caplog:
        resp = await test_cli.get("/test_get")
        assert resp.status == 200

        # We should get no access logging
        for log_record in caplog.records:
            if log_record.name != "sanic.access":
                continue

            # Check log record has data passed from access logging middleware
            assert hasattr(log_record, "request")
            assert hasattr(log_record, "response")
            assert hasattr(log_record, "time")
            assert hasattr(log_record, "req_id")


async def test_json_access_logging_no_ua(test_cli, logs):
    """
    GET request
    """
    formatter = JSONReqFormatter()

    with logs("sanic.access") as caplog:
        resp = await test_cli.get("/test_get", skip_auto_headers=["User-Agent"])
        assert resp.status == 200

        for log_record in caplog.records:
            if log_record.name != "sanic.access":
                continue

            rec = formatter.format(log_record)
            rec = json.loads(rec)
            assert rec["method"] == "GET"
            assert rec["user_agent"] is None


async def test_json_custom_class_logging(custom_class_log_test_cli, logs):
    """
    GET request
    """
    formatter = JSONFormatter()

    with logs("sanic.access") as caplog:
        resp = await custom_class_log_test_cli.get("/test_get")
        assert resp.status == 200

        for log_record in caplog.records:
            if log_record.name == "sanic.access":
                continue

            rec = formatter.format(log_record)
            rec = json.loads(rec)
            assert rec["message"] == "my class"
