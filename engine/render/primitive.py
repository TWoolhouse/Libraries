from vector import Vector
import engine.error

__all__ = ["Primative"]

class Primitive:

    def __init__(self):
        self._widget = None
        self._rendered = False

    def __hash__(self) -> int:
        return id(self)

    def update(self):
        self._widget = None

    def render(self, canvas):
        raise engine.error.render.PrimitiveError(self, "Can not be Rendered") from None

    def Transform(self, translate: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        raise engine.error.render.PrimitiveError(self, "Can not Transform") from None

    def _volatile(self, other) -> bool:
        """Equality Operation"""
        return False

    def __str__(self) -> str:
        string = self.__repr__()
        if string:
            return "Primative<{}: {}>".format(self.__class__.__name__, string)
        return "Primative<{}>".format(self.__class__.__name__)
    def __repr__(self) -> str:
        return ""