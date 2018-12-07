import asyncio
import logging
import logging.config
import time
import uuid

from sanic_json_logging.formatters import LOGGING_CONFIG_DEFAULTS
from sanic_json_logging.sanic_app import NoAccessLogSanic


__version__ = '0.3.5'
__all__ = ['setup_json_logging', 'NoAccessLogSanic']


def setup_json_logging(app, configure_task_local_storage=True, context_var='context'):
    """
    Sets up request logging
    """
    # Set up logging
    LOGGING_CONFIG_DEFAULTS['formatters']['generic']['context'] = context_var
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)

    if configure_task_local_storage:
        # Set task factory
        asyncio.get_event_loop().set_task_factory(lambda loop, coro: _task_factory(loop, coro, context_var))

    req_logger = logging.getLogger('sanic.access')

    # Middleware to start a timer to gather request length.
    # Also generate a request ID, should really make request ID configurable
    @app.middleware('request')
    async def log_json_pre(request):
        """
        Setup unique request ID and start time
        :param request: Web request
        """
        current_task = asyncio.Task.current_task()
        if current_task:
            if hasattr(current_task, 'context'):
                current_task.context['req_id'] = str(uuid.uuid4())
                current_task.context['req_start'] = time.perf_counter()
            else:
                current_task.context = {
                    'req_id': str(uuid.uuid4()),
                    'req_start': time.perf_counter()
                }

    # This performs the role of access logs
    @app.middleware('response')
    async def log_json_post(request, response):
        """
        Calculate response time, then log access json
        :param request: Web request
        :param response: HTTP Response
        :return:
        """
        req_id = 'unknown'
        time_taken = -1

        current_task = asyncio.Task.current_task()
        if current_task and hasattr(current_task, 'context'):
            req_id = current_task.context['req_id']
            time_taken = time.perf_counter() - current_task.context['req_start']

        req_logger.info(None, extra={'request': request, 'response': response, 'time': time_taken, 'req_id': req_id})


def _task_factory(loop, coro, context_var='context') -> asyncio.Task:
    """
    Task factory function
    Fuction closely mirrors the logic inside of
    asyncio.BaseEventLoop.create_task. Then if there is a current
    task and the current task has a context then share that context
    with the new task
    """
    task = asyncio.Task(coro, loop=loop)
    if task._source_traceback:  # flake8: noqa
        del task._source_traceback[-1]  # flake8: noqa

    # Share context with new task if possible
    current_task = asyncio.Task.current_task(loop=loop)
    if current_task is not None and hasattr(current_task, context_var):
        setattr(task, context_var, current_task.context)

    return task
