import sanic
import warnings


class NoAccessLogSanic(sanic.Sanic):
    def __init__(self, *args, **kwargs):
        super(NoAccessLogSanic, self).__init__(*args, **kwargs)

        self.config.LOGO = None
        self.config.ACCESS_LOG = None
        warnings.warn("Will be removed in v3.0.0, `app.config.ACCESS_LOG = None` will disable the access log",
                      DeprecationWarning)
