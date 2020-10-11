from ... import error
from ..entity import Entity
from ..component import Component

__all__ = ["Parent"]

class Parent(Component):

    def __init__(self, parent: Entity):
        self._parent = parent

    def parent(self, err=True) -> Entity:
        if self._parent is None and err:
            raise error.ecs.ParentError(self.entity)
        return self._parent

    def __repr__(self) -> str:
        return f"{super().__repr__()}<{self._parent}>"