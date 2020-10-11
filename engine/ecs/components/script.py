from ..entity import Entity
from ..component import Component
from ...core.application import app as Application

__all__ = ["Script"]

class Script(Component):

    def __init__(self):
        pass

    def initialize(self):
        self.__world = Application().world
        self.__world._script_components.add(self)

    def update(self):
        pass

    def terminate(self):
        self.__world._script_components.discard(self)