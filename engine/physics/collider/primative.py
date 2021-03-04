import enum
import functools
from vector import Vector
from ...ecs.components.collider import Collider
from typing import Callable

__all__ = ["detect", "Point", "Plane", "Rectangle", "Circle"]

@enum.unique
class Shape(enum.Enum):
    Point = 1
    Plane = 2
    Rectangle = 3
    Circle = 4

Point = Shape.Point
Plane = Shape.Plane
Rectangle = Shape.Rectangle
Circle = Shape.Circle

def detect(c1: Collider, c2: Collider) -> bool:
    return _d_detect_funcs[c1.shape][c2.shape](c1, c2)

def rside(func: Callable[[Collider, Collider], bool]) -> Callable[[Collider, Collider], bool]:
    @functools.wraps(func)
    def _rside(c1: Collider, c2: Collider) -> bool:
        return func(c2, c1)
    return rside

def _d_default(c1: Collider, c2: Collider) -> bool:
    return c1.transform == c2.transform

def _d_point_point(c1: Collider, c2: Collider) -> bool:
    return c1.transform.position_global == c2.transform.position_global

def _d_point_rectangle(c1: Collider, c2: Collider) -> bool:
    rect, r_half = c2.transform.position_global, c2.transform.scale_global / 2
    p = c1.transform.position_global
    bl, tr = rect - r_half, rect + r_half,
    return (p[0] > bl[0]) and (p[1] > bl[1]) and (p[0] < tr[0]) and (p[1] < tr[1])

def _d_rectangle_rectangle(c1: Collider, c2: Collider) -> bool:
    r1, r2 = c1.transform.position_global, c2.transform.position_global
    r1h, r2h = c1.transform.scale_global / 2, c2.transform.scale_global / 2
    return (r1[0] - r1h[0]) < (r2[0] + r2h[0]) and (r1[0] + r1h[0]) > (r2[0] - r2h[0]) and (r1[1] - r1h[1]) < (r2[1] + r2h[1]) and (r1[1] + r1h[1]) > (r2[1] - r2h[1])

_d_detect_funcs = {
    Shape.Point: {
        Shape.Point: _d_point_point,
        Shape.Plane: _d_default,
        Shape.Rectangle: _d_point_rectangle,
        Shape.Circle: _d_default,
    }, Shape.Plane: {
        Shape.Point: _d_default,
        Shape.Plane: _d_default,
        Shape.Rectangle: _d_default,
        Shape.Circle: _d_default,
    }, Shape.Rectangle: {
        Shape.Point: rside(_d_point_rectangle),
        Shape.Plane: _d_default,
        Shape.Rectangle: _d_rectangle_rectangle,
        Shape.Circle: _d_default,
    }, Shape.Circle: {
        Shape.Point: _d_default,
        Shape.Plane: _d_default,
        Shape.Rectangle: _d_default,
        Shape.Circle: _d_default,
    },
}
