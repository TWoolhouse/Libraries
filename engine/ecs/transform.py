from engine.ecs.component import Component
from vector import Vector
from engine.ecs.parent import Parent

class Transform(Component):
    def __init__(self, position: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        self._position = position
        self._rotation = rotation
        self._scale = scale

    def initialize(self) -> bool:
        self.parent = parent.entity if (parent := self.Check(Parent)) is not None else None
        return True

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
        self._position = value
    @rotation.setter
    def rotation(self, value: float):
        self._rotation = value
    @scale.setter
    def scale(self, value: Vector):
        self._scale = value

    @property
    def position_global(self) -> Vector:
        return self.parent.component(Transform).position_global + self._position if self.parent is not None else self._position
    @property
    def rotation_global(self) -> float:
        return parent.component(Transform).rotation_global + self._rotation if self.parent is not None else self._rotation
    @property
    def scale_global(self) -> Vector:
        return self.parent.component(Transform).scale_global.map(self._scale) if self.parent is not None else self._scale

    def __str__(self) -> str:
        return "{} {} {}".format(self.position, self.rotation, self.scale)