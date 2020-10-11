from .._settings import collider

class Settings:

    def __init__(self):
        pass

    def collision(self) -> collider.Setting:
        pass # Set Callback

    def _callback(self, func):
        def wrap_settings(*args, **kwargs):
            return func(self, *args, **kwargs)
        return wrap_settings