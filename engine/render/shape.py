from .primitive import Primitive
from vector import Vector

__all__ = ["Polygon"]

class Polygon(Primitive):

    def __init__(self, *pos: Vector):
        super().__init__()
        self.pos = pos
        self.unpacked = tuple((j for i in  self.pos for j in i))

    def render(self, canvas):
        return canvas.create_polygon(*self.unpacked)

    def Transform(self, translate: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        return self.__class__(*(v.rotate(rotation).map(scale) + translate for v in self.pos))

    def _volatile(self, other) -> bool:
        return all((i == j for i,j in zip(self.pos, other.pos)))

    @classmethod
    def Quad(self, width: int=1, height: int=1, skew: float=0.0, centre=True, hollow: float=0.0):
        if centre:
            poly = self(Vector(-0.5, -0.5), Vector(0.5, -0.5), Vector(0.5, 0.5), Vector(-0.5, 0.5))
        else:
            poly = self(Vector(0, 0), Vector(1, 0), Vector(1, 1), Vector(0, 1))
        if hollow:
            hollow /= 2
            poly = self(*poly.pos, poly.pos[0] + Vector(0, hollow), poly.pos[0] + Vector(hollow, hollow), poly.pos[3] + Vector(hollow, -hollow), poly.pos[2] - Vector(hollow, hollow), poly.pos[1] + Vector(-hollow, hollow), poly.pos[0] + Vector(0, hollow))
        return poly.Transform(rotation=skew, scale=Vector(width, height))

    @classmethod
    def Circle(self, radius: float=1.0, centre=True, res=1):
        if centre:
            vec = Vector(0, -1.0)
        return self(*(vec.rotate(angle) for angle in range(0, 360, int(res)))).Transform(scale=Vector(radius, radius))