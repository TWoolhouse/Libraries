from engine.ecs.component import Component
from engine.ecs.world import World
import engine.event

class Event(Component):
    def __init__(self, type=engine.event.Event, func=lambda self, event: None):
        self._event_type = type
        self._func = func
        World.active().Data().event_handles.append(self)

    def event(self, event: engine.event.Event):
        self._func(event)

    def terminate(self):
        World.active().Data().event_handles.remove(self)
        return True