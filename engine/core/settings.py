from .._settings import collider, render
from typing import Callable, T

class Settings:

    def __init__(self):
        pass

    def collision(self) -> collider.Setting:
        pass # Set Callback
    def render(self) -> render.Setting:
        pass # Set Callback

    def _callback(self, func: Callable[..., T]) -> Callable[..., T]:
        def wrap_settings(*args, **kwargs) -> T:
            return func(self, *args, **kwargs)
        return wrap_settings
