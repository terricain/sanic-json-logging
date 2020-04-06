import asyncio
import logging
import logging.config
import time
import uuid

from sanic_json_logging.formatters import LOGGING_CONFIG_DEFAULTS


__version__ = '3.1.0'
__all__ = ['setup_json_logging']


def setup_json_logging(app, configure_task_local_storage=True,
                       context_var='sanicjsonlogging',
                       disable_json_access_log=False):
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
        req_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        request['req_id'] = req_id
        request['req_start'] = start_time

        if configure_task_local_storage:
            current_task = asyncio.Task.current_task()
            if current_task:
                if hasattr(current_task, context_var):
                    if isinstance(getattr(current_task, context_var), dict):  # Guard against different non-dict context objs
                        getattr(current_task, context_var)['req_id'] = req_id
                        getattr(current_task, context_var)['req_start'] = start_time
                else:
                    setattr(current_task, context_var, {
                        'req_id': req_id,
                        'req_start': time.perf_counter()
                    })

    if not disable_json_access_log:
        # Prevent
        app.config.ACCESS_LOG = False

        # This performs the role of access logs
        @app.middleware('response')
        async def log_json_post(request, response):
            """
            Calculate response time, then log access json
            :param request: Web request
            :param response: HTTP Response
            :return:
            """
            # Pre middleware doesnt run on exception
            if 'req_id' in request:
                req_id = request['req_id']
                time_taken = time.perf_counter() - request['req_start']
            else:
                req_id = str(uuid.uuid4())
                time_taken = -1

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
        setattr(task, context_var, getattr(current_task, context_var))

    return task
