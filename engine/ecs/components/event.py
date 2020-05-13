from engine.ecs.entity import Entity
from engine.ecs.component import Component
from engine.core.application import app as Application

from engine.core.layer import Data as LayerData


__all__ = ["Event"]

class Event(Component):

    def __init__(self, func: callable, type: str="CONTROL", enabled: bool=True):
        self.__func, self.__type, self.__enabled = func, type, enabled

    def initialize(self):
        self._s_app_world = Application().world
        self.layer_data = LayerData(getattr(self._s_app_world.events.type, self.__type), self.__func, self.__enabled)
        self._s_app_world.events.add(self.layer_data)
        self._s_app_world.events.compile()

    def terminate(self):
        self._s_app_world.events.remove(self.layer_data)
        self._s_app_world.events.compile()

    def func(self, func: callable):
        try:
            self.layer_data.func = func
        except AttributeError:
            self.__func = func

    def toggle(self, flag: bool=None) -> bool:
        try:
            return self._s_app_world.events.activate(self.layer_data, flag)
        except AttributeError:
            self.__enabled = flag if isinstance(flag, bool) else not self.__enabled