import logging

import sanic.request
import sanic.response

from sanic_json_logging import setup_json_logging

app = sanic.Sanic("app1")
setup_json_logging(app, context_var="test1")

logger = logging.getLogger("root")


async def log():
    logger.info("some informational message")


@app.route("/endpoint1", methods=["GET"])
async def endpoint1(request: sanic.request.Request) -> sanic.response.BaseHTTPResponse:
    await log()
    return sanic.response.text("")


app.run()
