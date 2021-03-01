import enum
from vector import Vector
from . import collider as _phys_collider
from ..ecs.components.collider import Collider
# from ..core.application import app as Application
from .._settings.collider import Setting
from typing import Iterable

__all__ = ["SweepPrune"]

class _SPRef:
    def __init__(self, state: int, collider: Collider, axis: int):
        self.state = state # 0 Begining, 1 End
        self.collider = collider
        self.axis = axis
        self._value: float = None

    @property
    def value(self) -> float:
        if self._value is None:
            # Should work for collider types: Point, Rect, Circle
            self._value = self.collider.transform.position_global[self.axis] + (-self.collider.transform.scale_global[self.axis] if self.state else self.collider.transform.scale_global[self.axis])
        return self._value

    def __lt__(self, other: '_SPRef') -> bool:
        # if self.value == other.value: # Too unlikely to happen and shouldn't cause bugs?
        #     # Handling edge case of 2 colliders sharing the same point
        #     return
        return self.value < other.value

class SweepPrune:
    def __init__(self, axis: int=0):
        self._axis = axis
        self._colliders: dict[Collider, tuple[_SPRef]] = {}
        self._collider_order: list[_SPRef] = []

    def detect(self, mask: dict[int, set[int]], *colliders: Collider) -> Iterable[tuple[Collider, Collider]]:
        colliders: set[Collider] = set(colliders)
        acolliders = self._colliders.keys()
        # Colliders to remove
        for c in acolliders - colliders:
            for r in self._colliders[c]:
                self._collider_order.remove(r)
            del self._colliders[c]
        # Colliders to add
        for c in colliders - acolliders:
            refs = self._colliders[c] = (
                _SPRef(0, c, self._axis),
                _SPRef(1, c, self._axis),
            )
            self._collider_order.extend(refs)

        for c in self._collider_order:
            c._value = None # Reset the cached values
        self._collider_order.sort()

        hit: list[tuple[Collider, Collider]] = []
        active: set[Collider] = set()
        for ref in self._collider_order:
            if ref.state: # End
                active.discard(ref.collider)
            else: # Begin
                hit.extend(((ref.collider, c) for c in active if Masking.collide(mask, ref.collider, c)))
                active.add(ref.collider)
        return hit

    __call__ = detect

    def clear(self):
        for c in acolliders - colliders:
            for r in self._colliders[c]:
                self._collider_order.remove(r)
            del self._colliders[c]

    @property
    def axis(self) -> int:
        return self._axis
    @axis.setter
    def axis(self, value: int) -> int:
        if self._axis != value:
            self._axis = value
            self.clear()
        return self._axis
