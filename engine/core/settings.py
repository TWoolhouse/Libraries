from .._settings import collider, render
from typing import Callable, T
from ..error import SettingError
class Settings:

    def __init__(self):
        pass

    def collision(self) -> collider.Setting:
        raise SettingError(self.collision.__qualname__, "Not Instatiated")
    def render(self) -> render.Setting:
        raise SettingError(self.render.__qualname__, "Not Instatiated")

    def _callback(self, func: Callable[..., T]) -> Callable[..., T]:
        def wrap_settings(*args, **kwargs) -> T:
            return func(self, *args, **kwargs)
        return wrap_settings
