from engine.ecs.entity import Entity
from engine.ecs.component import Component
from engine.ecs.core.transform import Transform
from engine.core.application import app as Application

__all__ = ["Collider"]

class Collider(Component):

    def __init__(self, shape, transform: Transform, *layers: int):
        self.shape = shape
        self.transform = transform
        self.layers = layers
        self.collision = set()

    def initialize(self):
        self._child_entity = Application().world.instantiate(parent=self.entity, transform=self.transform, id=False)