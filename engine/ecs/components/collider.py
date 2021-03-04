import layer
from ..entity import Entity
from ..component import Component
from ..core.transform import Transform
from ...core.application import app as Application

__all__ = ["Collider"]

class Collider(Component):

    def __init__(self, shape: 'physics.colldier.Shape', transform: Transform, *layers: layer.Type):
        self.shape = shape
        self.transform = transform
        self.layers: set[layer.Type] = set(layers)
        self.collision: set[Collider] = set()

    def initialize(self):
        self.__world = Application().world
        self.__entity = self.__world.instantiate(parent=self.entity, transform=self.transform, id=False)

    def terminate(self):
        self.__world.destroy(self.__entity)
