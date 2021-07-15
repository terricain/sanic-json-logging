import logging

from contextlib import contextmanager

import pytest
import sanic

from sanic import response

from sanic_json_logging import _task_factory, setup_json_logging


# For testing raw access log suppression
@pytest.fixture
def no_log_app():
    # Create app
    app = sanic.Sanic("test_sanic_app")

    logger = logging.getLogger("root")

    @app.route("/test_get", methods=["GET"])
    async def test_get(request):
        logger.info("some informational message", extra={"test1": "test"})
        return response.text("")

    yield app


@pytest.fixture
def no_log_test_cli(loop, no_log_app, sanic_client):
    return loop.run_until_complete(sanic_client(no_log_app))


@pytest.fixture(autouse=True)
def set_task_factory(loop):
    loop.set_task_factory(_task_factory)


# For testing json
@pytest.fixture
def app():
    # Create app
    app = sanic.Sanic("test_sanic_app")
    setup_json_logging(app)

    logger = logging.getLogger("root")

    async def log():
        logger.info("some informational message", extra={"test1": "test"})

    @app.route("/test_get", methods=["GET"])
    async def test_get(request):
        await log()
        return response.text("")

    yield app


@pytest.fixture
def test_cli(loop, app, sanic_client):
    return loop.run_until_complete(sanic_client(app))


@pytest.fixture
def custom_class_log_app():
    # Create app
    app = sanic.Sanic("test_sanic_app")

    logger = logging.getLogger("root")

    @app.route("/test_get", methods=["GET"])
    async def test_get(request):
        class MyClass:
            def __str__(self):
                return "my class"

        logger.info(MyClass())
        return response.text("")

    yield app


@pytest.fixture
def custom_class_log_test_cli(loop, custom_class_log_app, sanic_client):
    return loop.run_until_complete(sanic_client(custom_class_log_app))


# For testing alternate context_var
@pytest.fixture
def app_alt():
    # Create app
    app = sanic.Sanic("test_sanic_app")
    setup_json_logging(app, context_var="test1")

    logger = logging.getLogger("root")

    async def log():
        logger.info("some informational message", extra={"test1": "test"})

    @app.route("/test_get", methods=["GET"])
    async def test_get(request):
        await log()
        return response.text("")

    yield app


@pytest.fixture
def test_alt_cli(loop, app_alt, sanic_client):
    return loop.run_until_complete(sanic_client(app_alt))


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
