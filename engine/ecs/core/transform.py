from engine.ecs.entity import Entity
from engine.ecs.component import Component
from vector import Vector

import engine.error
from engine.ecs.core.parent import Parent

__all__ = ["Transform"]

class Transform(Component):

    def __init__(self, pos: Vector=Vector(0.0, 0.0), rot: float=0.0, scl: Vector=Vector(1.0, 1.0)):
        self.position = pos
        self.rotation = rot
        self.scale = scl

    def initialize(self):
        try:
            self.parent = self.Get(Parent).parent().Get(Transform)
        except engine.error.ecs.ParentError:
            self.parent = None

    @property
    def position_global(self):
        return self.parent.position_global + self.position if self.parent else self.position
    @property
    def rotation_global(self):
        return self.parent.rotation_global + self.rotation if self.parent else self.rotation
    @property
    def scale_global(self):
        return self.scale.map(self.parent.scale_global) if self.parent else self.scale

    def __repr__(self) -> str:
        return f"{super().__repr__()}<{self.position} {self.rotation} {self.scale}>"