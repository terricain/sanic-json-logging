import logging
from contextlib import contextmanager

from sanic import response
import pytest

from sanic_json_logging import NoAccessLogSanic, setup_json_logging, _task_factory


# For testing raw access log suppression
@pytest.fixture
def no_log_app():
    # Create app
    app = NoAccessLogSanic("test_sanic_app")

    logger = logging.getLogger('root')

    @app.route("/test_get", methods=['GET'])
    async def test_get(request):
        logger.info('some informational message', extra={'test1': 'test'})
        return response.text('')

    yield app


@pytest.fixture
def no_log_test_cli(loop, no_log_app, test_client):
    return loop.run_until_complete(test_client(no_log_app))


@pytest.fixture(autouse=True)
def set_task_factory(loop):
    loop.set_task_factory(_task_factory)


# For testing json
@pytest.fixture
def app():
    # Create app
    app = NoAccessLogSanic("test_sanic_app")
    setup_json_logging(app)

    logger = logging.getLogger('root')

    async def log():
        logger.info('some informational message', extra={'test1': 'test'})

    @app.route("/test_get", methods=['GET'])
    async def test_get(request):
        await log()
        return response.text('')

    yield app


@pytest.fixture
def test_cli(loop, app, test_client):
    return loop.run_until_complete(test_client(app))


# For testing alternate context_var
@pytest.fixture
def app_alt():
    # Create app
    app = NoAccessLogSanic("test_sanic_app")
    setup_json_logging(app, context_var='test1')

    logger = logging.getLogger('root')

    async def log():
        logger.info('some informational message', extra={'test1': 'test'})

    @app.route("/test_get", methods=['GET'])
    async def test_get(request):
        await log()
        return response.text('')

    yield app


@pytest.fixture
def test_alt_cli(loop, app_alt, test_client):
    return loop.run_until_complete(test_client(app_alt))


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
