from engine.ecs.entity import Entity
from engine.ecs.component import Component
from engine.core.application import app as Application

__all__ = ["Script"]

class Script(Component):

    def __init__(self):
        pass

    def initialize(self):
        self._s_app_world = Application().world
        self._s_app_world._script_components.add(self)

    def update(self):
        pass

    def terminate(self):
        self._s_app_world._script_components.discard(self)