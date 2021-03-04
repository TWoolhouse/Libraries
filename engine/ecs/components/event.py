from ..entity import Entity
from ..component import Component
from ...core.application import app as Application
from typing import Callable
from ...event import Event as Eevent

from layer import Data as LayerData


__all__ = ["Event"]

class Event(Component):

    def __init__(self, func: Callable[[Eevent], None], type: str="CONTROL", enabled: bool=True):
        self.__func, self.__type, self.__enabled = func, type, enabled

    def initialize(self):
        self.__world = Application().world
        self.layer_data = LayerData(getattr(self.__world.events.type, self.__type), self.__func, self.__enabled)
        self.__world.events.add(self.layer_data)
        self.__world.events.compile()

    def terminate(self):
        self.__world.events.remove(self.layer_data)
        self.__world.events.compile()

    def func(self, func: Callable[[Eevent], None]):
        try:
            self.layer_data.func = func
        except AttributeError:
            self.__func = func

    def toggle(self, flag: bool=None) -> bool:
        try:
            return self.__world.events.activate(self.layer_data, flag)
        except AttributeError:
            self.__enabled = flag if isinstance(flag, bool) else not self.__enabled
