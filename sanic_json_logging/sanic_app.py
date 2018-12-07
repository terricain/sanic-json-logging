import sanic


class NoAccessLogSanic(sanic.Sanic):
    def __init__(self, *args, **kwargs):
        super(NoAccessLogSanic, self).__init__(*args, **kwargs)

        # The logo is cool... just not in my logs
        self.config.LOGO = None

    def run(self, *args, **kwargs):
        if 'access_log' not in kwargs:
            kwargs['access_log'] = False
        return super(NoAccessLogSanic, self).run(*args, **kwargs)

    def _helper(self, *args, **kwargs):
        result = super(NoAccessLogSanic, self)._helper(*args, **kwargs)
        result['access_log'] = False
        return result
