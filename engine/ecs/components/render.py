from engine.ecs.entity import Entity
from engine.ecs.component import Component

from engine.ecs.core.transform import Transform
from engine.render.primitive import Primitive

__all__ = ["Render"]

class Render(Component):

    def __init__(self, primative: Primitive, volatile=False):
        self._original = primative
        self._drawn = self._original

        self._vcache = self._original.Transform() if volatile else False

        self._update = True

    def update(self):
        self._update = True

    def initialize(self):
        self.transform = self.Get(Transform)
        self._u_transform()
        self._u_drawn_primative()
        self.update()

    def _u_transform(self):
        self._global_transform = (self.transform.position_global, self.transform.rotation_global, self.transform.scale_global)
        return self._global_transform

    def _u_drawn_primative(self):
        self._drawn = self._original.Transform(*self._global_transform)

    def _volatile(self) -> bool:
        if self._original._volatile(self._vcache):
            return False
        self._vcache = self._original.Transform()
        return True

    def primative(self) -> Primitive:
        return self._original

    def __repr__(self) -> str:
        return f"{super().__repr__()}<{self._original}>"