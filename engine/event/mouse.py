from vector import Vector
from .event import Event
from ..input import mouses as imouse, Mouse as IMouse

__all__ = ["Mouse", "MouseButton", "MousePress", "MouseRelease"]

class Mouse(Event):
    pass

class MouseButton(Mouse):

    def __init__(self, button, x: int, y: int):
        super().__init__()
        self.button = imouse.Mouse(button)
        self.pos = Vector(x, y)

    def __repr__(self) -> str:
        return "{} {}".format(self.button, self.pos)

class MousePress(MouseButton):
    def __init__(self, button, x: int, y: int):
        super().__init__(button, x, y)
        imouse._mouse[button] = True
class MouseRelease(MouseButton):
    def __init__(self, button, x: int, y: int):
        super().__init__(button, x, y)
        imouse._mouse[button] = False

class MouseMove(Mouse):

    def __init__(self, x: int, y: int):
        super().__init__()
        self.pos = Vector(x, y)
        imouse._mouse[IMouse.POS] = self.pos

    def __repr__(self) -> str:
        return self.pos.__repr__()