==================
sanic-json-logging
==================

.. image:: https://img.shields.io/pypi/v/sanic-json-logging.svg
        :target: https://pypi.python.org/pypi/sanic-json-logging

.. image:: https://travis-ci.com/terrycain/sanic-json-logging.svg?branch=master
        :target: https://travis-ci.com/terrycain/sanic-json-logging

.. image:: https://codecov.io/gh/terrycain/sanic-json-logging/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/terrycain/sanic-json-logging
        :alt: Code coverage

.. image:: https://pyup.io/repos/github/terrycain/sanic-json-logging/shield.svg
     :target: https://pyup.io/repos/github/terrycain/sanic-json-logging/
     :alt: Updates

The other day I was running some containers on Amazon's ECS and logging to cloudwatch. I then learnt cloudwatch parses JSON logs so
obviously I then wanted Sanic to log out JSON.

Ideally this'll be useful to people but if it isn't, raise an issue and we'll make it better :)

To install:

.. code-block:: bash

    pip install sanic-json-logging

Look at ``examples/simple.py`` for a full working example, but this will essentially get you going

.. code-block:: python

    import sanic
    from sanic_json_logging import setup_json_logging

    app = sanic.Sanic()
    setup_json_logging(app)


``setup_json_logging`` does the following:

- changes the default log formatters to JSON ones
- also filters out no Keepalive warnings
- unless told otherwise, will change the asyncio task factory, to implement some rudimentary task-local storage.
- installs pre and post request middleware. Pre-request middleware to time tasks and generate a uuid4 request id. Post-request middleware to emit access logs.
- will use AWS X-Forwarded-For IPs in the access logs if present

If ``setup_json_logging`` changed the task factory, all tasks created from the request's task will contain the request ID.
You can pass ``disable_json_access_log=True`` to the setup function which will disable the configuration of JSON access logging.
Setting ``configure_task_local_storage`` to false will disable storing request IDs inside the task object which will

Currently I have it outputting access logs like

.. code-block:: json

    {
      "timestamp": "2018-06-09T17:42:52.195701Z",
      "level": "INFO",
      "method": "GET",
      "path": "/endpoint1",
      "remote": "127.0.0.1:33468",
      "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36",
      "host": "localhost:8000",
      "response_time": 0.0,
      "req_id": "795617c7-b514-4ed9-bb63-cc4fcd883c3d",
      "logger": "sanic.access",
      "status_code": 200,
      "length": 0,
      "type": "access"
    }

And if you log to the ``root`` logger, inside a request, it'll look like this.

.. code-block:: json

    {
      "timestamp": "2018-06-09T17:42:52.195326Z",
      "level": "INFO",
      "message": "some informational message",
      "type": "log",
      "logger": "root",
      "filename": "simple.py",
      "lineno": 16,
      "req_id": "795617c7-b514-4ed9-bb63-cc4fcd883c3d"
    }

Changelog
---------

1.3.0 - Added Request ID to `request` dict, fixed move to travis.com

1.2.0 - Fixed UA header bug, fixed tests

1.1.1 - Pretty much first decent version
