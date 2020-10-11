from ..entity import Entity
from ..component import Component
from .event import Event
from ..core.transform import Transform
from vector import Vector
from ...enums.mouse import Mouse as IMouse
from ...core.application import app as Application
from ...event.mouse import Mouse as MouseEvent, MousePress as MousePressEvent

class Button(Component):

    def __init__(self, func, size: Vector, key: IMouse=IMouse.B1, block: bool=True, event: MouseEvent=MousePressEvent):
        self.func = func
        self.size = (-size / 2, size / 2)
        self.key = key
        self.block = block
        self.event_type = event

    def initialize(self):
        self.__transform = self.Get(Transform)
        self.event = Event(self.__event_handle)
        self.__world = Application().world
        self.__entity = self.__world.instantiate(self.event, parent=self.entity, id=False)

    def terminate(self):
        self.__world.destroy(self.__entity)

    def __event_handle(self, event: MouseEvent):
        if event.dispatch(self.event_type) and event.button is self.key:
            pos = self.__transform.position_global
            if event.pos.within(*zip(pos + self.size[0], pos + self.size[1]), include=True):
                event.handled = self.block
                return self.func()