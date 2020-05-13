from engine.render.primitive import Primitive
from vector import Vector

__all__ = ["Text"]

class Text(Primitive):
    def __init__(self, string: str):
        super().__init__()
        self.pos = Vector(0, 0)
        self.text = string

    def render(self, canvas):
        return canvas.create_text(*self.pos, text=self.text)

    def Transform(self, translate: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        new = self.__class__(self.text)
        new.pos = self.pos.rotate(rotation).map(scale) + translate
        return new

    def _volatile(self, other) -> bool:
        return self.text == other.text

    def __repr__(self) -> str:
        return self.text