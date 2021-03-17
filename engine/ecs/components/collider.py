import layer
from typing import Union
from ..entity import Entity
from ..component import Component
from ..core.transform import Transform
from ...core.application import app as Application

__all__ = ["Collider"]

class Collider(Component):

    def __init__(self, shape: 'physics.colldier.Shape', transform: Transform, *layers: Union[layer.Type.Item, str]):
        self.shape = shape
        self.transform = transform
        lyrs = Application().setting.collision().layers
        self.layers: set[layer.Type] = set(l if isinstance(l, layer.Type.Item) else lyrs[l] for l in layers)
        self.collision: set[Collider] = set()

    def initialize(self):
        self.__world = Application().world
        self.__entity = self.__world.instantiate(parent=self.entity, transform=self.transform, id=False)

    def terminate(self):
        self.__world.destroy(self.__entity)
