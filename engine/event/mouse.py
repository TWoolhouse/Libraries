from vector import Vector
from engine.event.event import Event
import engine.input.mouses

__all__ = ["Mouse", "MouseButton", "MousePress", "MouseRelease"]

class Mouse(Event):
    pass

class MouseButton(Mouse):

    def __init__(self, button, x: int, y: int):
        self.button = engine.input.mouses.Mouse(button)
        self.pos = Vector(x, y)

    def __repr__(self) -> str:
        return "{} {}".format(self.button, self.pos)

class MousePress(MouseButton):
    def __init__(self, button, x: int, y: int):
        super().__init__(button, x, y)
        engine.input.mouses._mouse[button] = True
class MouseRelease(MouseButton):
    def __init__(self, button, x: int, y: int):
        super().__init__(button, x, y)
        engine.input.mouses._mouse[button] = False

class MouseMove(Mouse):

    def __init__(self, x: int, y: int):
        self.pos = Vector(x, y)
        engine.input.mouses._mouse[engine.input.Mouse.POS] = self.pos

    def __repr__(self) -> str:
        return self.pos.__repr__()