import asyncio
import logging
import logging.config
import sys
import time
import uuid

from typing import TYPE_CHECKING, Any, Generator

from sanic_json_logging.formatters import LOGGING_CONFIG_DEFAULTS

if TYPE_CHECKING:
    import sanic

__version__ = "0.0.0"
__all__ = ["setup_json_logging"]

PY_37 = sys.version_info[1] >= 7
if PY_37:
    current_task_func = asyncio.current_task
else:
    current_task_func = asyncio.Task.current_task


def setup_json_logging(
    app: "sanic.Sanic",
    configure_task_local_storage: bool = True,
    context_var: str = "sanicjsonlogging",
    disable_json_access_log: bool = False,
) -> None:
    """
    Sets up request logging
    """
    # Set up logging
    LOGGING_CONFIG_DEFAULTS["formatters"]["generic"]["context"] = context_var
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)

    if configure_task_local_storage:
        # Set task factory
        asyncio.get_event_loop().set_task_factory(lambda loop, coro: _task_factory(loop, coro, context_var))

    req_logger = logging.getLogger("sanic.access")

    # Middleware to start a timer to gather request length.
    # Also generate a request ID, should really make request ID configurable
    @app.middleware("request")  # type: ignore
    async def log_json_pre(request: "sanic.Request") -> None:
        """
        Setup unique request ID and start time
        :param request: Web request
        """
        req_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        request.ctx.req_id = req_id
        request.ctx.req_start = start_time

        if configure_task_local_storage:
            current_task = current_task_func()

            if current_task:
                if hasattr(current_task, context_var):
                    # Guard against different non-dict context objs
                    if isinstance(getattr(current_task, context_var), dict):
                        getattr(current_task, context_var)["req_id"] = req_id
                        getattr(current_task, context_var)["req_start"] = start_time
                else:
                    setattr(current_task, context_var, {"req_id": req_id, "req_start": time.perf_counter()})

    if not disable_json_access_log:
        # Prevent
        app.config.ACCESS_LOG = False

        # This performs the role of access logs
        @app.middleware("response")  # type: ignore
        async def log_json_post(request: "sanic.Request", response: "sanic.HTTPResponse") -> None:
            """
            Calculate response time, then log access json
            :param request: Web request
            :param response: HTTP Response
            :return:
            """
            # Pre middleware doesnt run on exception
            try:
                req_id = request.ctx.req_id
                time_taken = time.perf_counter() - request.ctx.req_start
            except Exception:
                req_id = str(uuid.uuid4())
                time_taken = -1

            req_logger.info(
                None, extra={"request": request, "response": response, "time": time_taken, "req_id": req_id}
            )


def _task_factory(
    loop: asyncio.AbstractEventLoop, coro: Generator[Any, None, Any], context_var: str = "context"
) -> asyncio.Task:
    """
    Task factory function
    Fuction closely mirrors the logic inside of
    asyncio.BaseEventLoop.create_task. Then if there is a current
    task and the current task has a context then share that context
    with the new task
    """
    task = asyncio.Task(coro, loop=loop)

    # Share context with new task if possible
    current_task = current_task_func(loop=loop)

    if current_task is not None and hasattr(current_task, context_var):
        setattr(task, context_var, getattr(current_task, context_var))

    return task
