import logging

import sanic.response
import sanic.request

from sanic_json_logging import setup_json_logging, NoAccessLogSanic


app = NoAccessLogSanic('app1')
setup_json_logging(app)

logger = logging.getLogger('root')


async def log():
    logger.info('some informational message')


@app.route("/endpoint1", methods=['GET'])
async def endpoint1(request: sanic.request.Request) -> sanic.response.BaseHTTPResponse:
    await log()
    return sanic.response.text('')

app.run()
