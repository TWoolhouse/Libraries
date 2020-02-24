from engine.ecs.entity import Entity
from engine.ecs.component import Component
from vector import Vector
import engine.render
import engine.physics

# Render = engine.render.Render()

class Parent(Component):
    def __init__(self, entity: Entity):
        self.entity = entity

class Transform(Component):
    def __init__(self, position: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        self._position = position
        self._rotation = rotation
        self._scale = scale

    @property
    def position(self) -> Vector:
        return self._position
    @property
    def rotation(self) -> float:
        return self._rotation
    @property
    def scale(self) -> Vector:
        return self._scale

    @position.setter
    def position(self, value: Vector):
        self.event(event.Transform(0))
        self._position = value
    @rotation.setter
    def rotation(self, value: float):
        self.event(event.Transform(1))
        self._rotation = value
    @scale.setter
    def scale(self, value: Vector):
        self.event(event.Transform(2))
        self._scale = value

    @property
    def position_global(self) -> Vector:
        return parent.component(Transform).position_global + self._position if (parent := self._entity._parent) else self._position
    @property
    def rotation_global(self) -> float:
        return parent.component(Transform).rotation_global + self._rotation if (parent := self._entity._parent) else self._rotation
    @property
    def scale_global(self) -> Vector:
        return parent.component(Transform).scale_global + self._scale if (parent := self._entity._parent) else self._scale

class Graphic(Component):

    events = {event.Transform,}

    def __init__(self, primative: engine.render.Primitive):
        self.original_primative = primative
        self.primative = self.original_primative
        self.transform = None

    def init(self) -> bool:
        self.transform = self.component(Transform)
        return True

    def update(self):
        engine.render.Render().submit(self.primative)

    def event_Transform(self, event: event.Transform):
        self.primative = self.original_primative.Transform(self.transform.position, self.transform.rotation, self.transform.scale)

class Collider(Component):

    events = {event.Transform,}

    def __init__(self, collider: engine.physics.collider.Collider):
        self.collider = collider
        self.flag = True

    def init(self) -> bool:
        self.transform = self.component(Transform)
        return True

    def event_Transform(self, event: event.Transform):
        self.flag = True