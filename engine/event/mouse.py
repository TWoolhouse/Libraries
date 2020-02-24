from vector import Vector
from engine.event.event import Event

__all__ = ["Mouse", "MouseButton", "MousePress", "MouseRelease"]

class Mouse(Event):
    pass

class MouseButton(Mouse):

    def __init__(self, button, x: int, y: int):
        self.button = button
        self.pos = Vector(x, y)
    
    def __repr__(self) -> str:
        return "{} {}".format(self.button, self.pos)

class MousePress(MouseButton):
    pass
class MouseRelease(MouseButton):
    pass

class MouseMove(Mouse):

    def __init__(self, x: int, y: int):
        self.pos = Vector(x, y)

    def __repr__(self) -> str:
        return self.pos.__repr__()