from .event import Event

__all__ = ["Window", "WindowClose", "WindowResize"]

class Window(Event):
    pass

class WindowClose(Window):
    pass

class WindowResize(Window):

    def __init__(self, width, height):
        super().__init__()
        self.width, self.height = width, height

    def __repr__(self) -> str:
        return "({}, {})".format(self.width, self.height)

class WindowFocus(Window):
    pass
class WindowFocusGain(WindowFocus):
    pass
class WindowFocusLose(WindowFocus):
    pass