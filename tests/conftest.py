import logging

from contextlib import contextmanager

import pytest
import sanic

from sanic import response
from sanic_testing import TestManager

from sanic_json_logging import _task_factory, setup_json_logging


@pytest.fixture(autouse=True)
def set_task_factory(loop):
    loop.set_task_factory(_task_factory)


# For testing json
@pytest.fixture
def generic_app():
    # Create app
    app = sanic.Sanic("generic_app")
    TestManager(app)
    setup_json_logging(app)

    logger = logging.getLogger("myapplogger")

    async def log():
        logger.info("some informational message", extra={"test1": "test"})

    @app.route("/test_get", methods=["GET"])
    async def test_get(request):
        await log()
        return response.text("")

    return app


@pytest.fixture
def custom_log_app():
    # Create app
    app = sanic.Sanic("custom_log_app")
    TestManager(app)
    setup_json_logging(app)

    logger = logging.getLogger("myapplogger")

    @app.route("/test_get", methods=["GET"])
    async def test_get(request):
        class MyClass:
            def __str__(self):
                return "my class"

        logger.info(MyClass())
        return response.text("")

    return app


@pytest.fixture
def logs(caplog):
    @contextmanager
    def _f(logger_name):
        caplog.clear()
        logger = logging.getLogger(logger_name)
        logger.addHandler(caplog.handler)
        yield caplog
        logger.removeHandler(caplog.handler)

    return _f
