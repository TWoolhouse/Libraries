from vector import Vector
import enum

__all__ = ["Point", "Rectangle", "Circle"]

def rside(func):
    def _rside(self, transform_s, other, transform_o):
        return func(other, transform_o, self, transform_s)
    return rside

class Collider:
    _funcs = {}

    def __init__(self, centre: Vector):
        self.pos = centre

    def detect(self, transform_s, other, transform_o) -> bool:
        return self._funcs[type(other)](self, transform_s, other, transform_o)

class Rectangle(Collider):

    def __init__(self, centre: Vector, width: float, height: float):
        super().__init__(centre)
        self.width, self.height = width, height
        self.width2, self.height2 = width / 2, height / 2

    def _rectangle(self, tfs, other, tfo):
        pass

for k,v in {
        Rectangle: Rectangle._rectangle,
    }.items():
    Rectangle._funcs[k] = v

class Point(Collider):

    def __init__(self, centre: Vector):
        super().__init__(centre)

    def _rectangle(self, tfs, other, tfo) -> bool:
        width, height = Vector(other.width2, other.height2).map(tfo.scale)
        return ((tfs.position_global + self.pos) - (tfo.position_global + other.pos)).within((-width, width), (-height, height))

for k,v in {
        Rectangle: Point._rectangle,
    }.items():
    Point._funcs[k] = v
for k,v in {
    Point: rside(Point._rectangle)
    }.items():
    Rectangle._funcs[k] = v