import asyncio
import datetime
import logging
import json
import sys
from collections import OrderedDict


LOGGING_CONFIG_DEFAULTS = dict(
    version=1,
    disable_existing_loggers=False,

    filters={
        'no_keepalive_timeout': {
            '()': 'sanic_json_logging.formatters.NoKeepaliveFilter'
        }
    },

    loggers={
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        },
        'sanic.error': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
            'qualname': 'sanic.error'
        },

        'sanic.access': {
            'level': 'INFO',
            'handlers': ['access_console'],
            'propagate': True,
            'qualname': 'sanic.access'
        }
    },
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': sys.stdout,
            'filters': ['no_keepalive_timeout']
        },
        'access_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'access',
            'stream': sys.stdout
        },
    },
    formatters={
        'generic': {
            'class': 'sanic_json_logging.formatters.JSONFormatter',
        },
        'access': {
            'class': 'sanic_json_logging.formatters.JSONReqFormatter'
        },
    }
)


# Gets rid of annoying info level messages where
# browser is sending connection keepalive header
class NoKeepaliveFilter(logging.Filter):
    def filter(self, record):
        return not record.msg.startswith('KeepAlive Timeout')


class JSONFormatter(logging.Formatter):
    def __init__(self, *args, context='context', **kwargs):
        super(JSONFormatter, self).__init__(*args, **kwargs)

        self._context_attr = context

    @staticmethod
    def format_timestamp(time):
        return datetime.datetime.utcfromtimestamp(time).isoformat() + 'Z'

    def format(self, record, serialize=True):
        try:
            msg = record.msg % record.args
        except TypeError:
            msg = record.msg

        try:
            msg_type = record.type
        except AttributeError:
            msg_type = 'log'

        # Deal with tracebacks
        exc = ''
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if exc[-1:] != '\n':
                exc += '\n'
            exc += record.exc_text
        if record.stack_info:
            if exc[-1:] != '\n':
                exc += '\n'
            exc += self.formatStack(record.stack_info)
        exc = exc.lstrip('\n').replace('\n', '<br>')

        message = OrderedDict((
            ('timestamp', self.format_timestamp(record.created)),
            ('level', record.levelname),
            ('message', msg),
            ('type', msg_type),
            ('logger', record.name),
        ))

        if msg_type == 'log':
            message['filename'] = record.filename
            message['lineno'] = record.lineno
        elif msg_type == 'event':
            message['event_type'] = record.event_type

        if len(exc) > 0:
            message['traceback'] = exc
            message['type'] = 'exception'
        if hasattr(record, 'data'):
            message['data'] = record.data

        try:
            current_task = asyncio.Task.current_task()
            # TODO make 'context' configurable by __init__(arg) from logging config
            if current_task and hasattr(current_task, 'context'):
                message['req_id'] = current_task.context.get('req_id', 'unknown')
        except Exception:
            pass

        # TODO log an error if json.dumps fails
        return json.dumps(message)


class JSONReqFormatter(JSONFormatter):
    def format(self, record, serialize=True):
        # Create message dict
        message = OrderedDict((
            ('timestamp', self.format_timestamp(record.created)),
            ('level', record.levelname),
            ('method', record.request.method),
            ('path', record.request.path),
            ('remote', '{0}:{1}'.format(record.request.ip, record.request.port)),
            ('user_agent', record.request.headers['user-agent']),
            ('host', record.request.host),
            ('response_time', round(record.time, 2)),
            ('req_id', record.req_id),
            ('logger', record.name)
        ))

        if record.response is not None:  # not Websocket
            message['status_code'] = record.response.status
            message['length'] = len(record.response.body)
            message['type'] = 'access'
        else:
            message['type'] = 'ws_access'

        # Can't remember why I added this
        if 'error_message' in record.request:
            try:
                message['request_info']['error_message'] = record.request['error_message']
            except KeyError:
                message['request_info'] = {'error_message': record.request['error_message']}

        return json.dumps(message)
