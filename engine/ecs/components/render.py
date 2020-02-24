from vector import Vector
from engine.ecs.component import Component
from engine.ecs.components import Transform
from engine.render import Primitive

class Render(Component):

    def __init__(self, primative: Primitive):
        self.original_primative = primative
        self.primative = self.original_primative
        self.transform = None
        self._render_transform = [Vector(0, 0), 0, Vector(1, 1)]
        self.update = False

    def initialize(self) -> bool:
        self.transform = self.Get(Transform)
        self._render_transform = [self.transform.position_global, self.transform.rotation_global, self.transform.scale_global]
        self.update_primative()
        return True

    def update_primative(self):
        self._render_transform = [self.transform.position_global, self.transform.rotation_global, self.transform.scale_global]
        self.primative = self.original_primative.Transform(*self._render_transform)
        self.update = False

    def __str__(self) -> str:
        return ""

    # def event_Transform(self, event: event.Transform):
    #     self.primative = self.original_primative.Transform(self.transform.position, self.transform.rotation, self.transform.scale)
    # def update(self):
    #     engine.render.Render().submit(self.primative)