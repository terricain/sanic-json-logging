import asyncio
import datetime
import json
import logging
import os
import sys

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

if TYPE_CHECKING:
    from sanic import HTTPResponse, Request

    class JSONLogRecord(logging.LogRecord):
        type: str
        request: Request
        response: HTTPResponse
        event_type: str
        time: Union[float, int]
        req_id: str
        data: Any


PY_37 = sys.version_info[1] >= 7

LOGGING_CONFIG_DEFAULTS: Dict[str, Any] = dict(
    version=1,
    disable_existing_loggers=False,
    filters={"no_keepalive_timeout": {"()": "sanic_json_logging.formatters.NoKeepaliveFilter"}},
    root={"level": "INFO", "handlers": ["console"]},
    loggers={
        "sanic.error": {"level": "INFO", "handlers": ["console"], "propagate": False, "qualname": "sanic.error"},
        "sanic.root": {"level": "INFO", "handlers": [], "propagate": False, "qualname": "sanic.root"},
        "sanic.access": {
            "level": "INFO",
            "handlers": ["access_console"],
            "propagate": False,
            "qualname": "sanic.access",
        },
    },
    handlers={
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stdout,
            "filters": ["no_keepalive_timeout"],
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": sys.stdout,
            "filters": ["no_keepalive_timeout"],
        },
    },
    formatters={
        "generic": {
            "class": "sanic_json_logging.formatters.JSONFormatter",
        },
        "access": {"class": "sanic_json_logging.formatters.JSONReqFormatter"},
    },
)


# Gets rid of annoying info level messages where
# browser is sending connection keepalive header
class NoKeepaliveFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            return "KeepAlive Timeout" not in record.msg
        except:  # noqa: E722
            return True


class JSONFormatter(logging.Formatter):
    def __init__(self, *args: Any, context_var: str = "context", **kwargs: Any) -> None:
        super(JSONFormatter, self).__init__(*args, **kwargs)

        self._context_attr: str = LOGGING_CONFIG_DEFAULTS["formatters"]["generic"].get("context", context_var)
        self._pid = os.getpid()

    @staticmethod
    def format_timestamp(time: Union[int, float]) -> str:
        return datetime.datetime.utcfromtimestamp(time).isoformat() + "Z"

    def format(self, record: logging.LogRecord) -> str:
        record = cast("JSONLogRecord", record)

        try:
            msg = record.msg % record.args
        except TypeError:
            msg = record.msg

        try:
            msg_type = record.type
        except AttributeError:
            msg_type = "log"

        # Deal with tracebacks
        exc = self.formatTraceback(record)

        # convert to string if not primitive JSON dump values
        # https://docs.python.org/3/library/json.html#json.JSONDecoder
        if type(msg) not in [dict, list, str, int, float, bool, None]:
            msg = str(msg)
        message = OrderedDict(
            (
                ("timestamp", self.format_timestamp(record.created)),
                ("level", record.levelname),
                ("message", msg),
                ("type", msg_type),
                ("logger", record.name),
                ("worker", self._pid),
            )
        )

        if msg_type == "log":
            message["filename"] = record.filename
            message["lineno"] = record.lineno
        elif msg_type == "event":
            message["event_type"] = record.event_type

        if exc:
            message["traceback"] = exc
            message["type"] = "exception"
        if hasattr(record, "data"):
            message["data"] = record.data

        try:
            if PY_37:
                current_task = asyncio.current_task()
            else:
                current_task = asyncio.Task.current_task()

            if current_task and hasattr(current_task, self._context_attr):
                message["req_id"] = getattr(current_task, self._context_attr).get("req_id", "unknown")
        except Exception:
            pass

        # TODO log an error if json.dumps fails
        return json.dumps(message)

    def formatTraceback(self, record: logging.LogRecord) -> Optional[str]:
        exc = ""
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if exc[-1:] != "\n":
                exc += "\n"
            exc += record.exc_text
        if record.stack_info:
            if exc[-1:] != "\n":
                exc += "\n"
            exc += self.formatStack(record.stack_info)
        exc = exc.lstrip("\n").replace("\n", "<br>")

        return None if not exc else exc


class JSONReqFormatter(JSONFormatter):
    def format(self, record: logging.LogRecord) -> str:
        record = cast("JSONLogRecord", record)

        # Create message dict
        try:
            host: Optional[str] = record.request.host
        except:  # noqa: E722
            # Got a few errors with curl :/
            host = None

        # Extract real ip if in AWS (or compatible)
        ip = record.request.headers.get("X-Forwarded-For", record.request.ip)
        port = record.request.headers.get("X-Forwarded-Port", record.request.port)

        message = OrderedDict(
            (
                ("timestamp", self.format_timestamp(record.created)),
                ("level", record.levelname),
                ("method", record.request.method),
                ("type", "access"),
                ("path", record.request.path),
                ("remote", "{0}:{1}".format(ip, port)),
                ("user_agent", record.request.headers.get("user-agent")),
                ("host", host),
                ("response_time", round(record.time, 2)),
                ("req_id", record.req_id),
                ("logger", record.name),
                ("worker", self._pid),
            )
        )

        if record.response is not None:  # not Websocket
            message["status_code"] = record.response.status
            if hasattr(record.response, "body") and record.response.body:
                message["length"] = len(record.response.body)
            else:
                message["length"] = -1

            message["type"] = "access"
        else:
            message["type"] = "ws_access"

        return json.dumps(message)


class JSONTracebackJSONFormatter(JSONFormatter):
    def formatTraceback(self, record: logging.LogRecord) -> Optional[str]:
        from boltons import tbutils

        if not hasattr(record, "exc_info") or record.exc_info is None or (record.exc_info and len(record.exc_info) < 3):
            return None

        return tbutils.ExceptionInfo.from_exc_info(*record.exc_info).to_dict()
