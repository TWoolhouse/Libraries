import tkinter as tk
from .. import event as Eevent
from vector import Vector
from typing import Callable, Any, T

__all__ = ["Window"]

def event(func: Callable[[T], None]) -> Callable[[T], str]:
    def event_binding(event: T) -> str:
        func(event)
        return "break"
    return event_binding

class Window:

    def __init__(self, callback: Callable[[Eevent.Event], Any]):
        """Manages the Window
        callback: The function for the event callback
        """
        self.callback = callback
        self._master = tk.Tk()
        self._master.protocol("WM_DELETE_WINDOW", self.__destroy)
        self.__size = Vector(1280, 720)
        self._canvas = tk.Canvas(self._master, width=self.__size[0], height=self.__size[1], bd=-2)
        self._canvas.pack(fill="both", expand=True)
        self.__bind()

    def initialize(self):
        self._canvas.focus_force()

    def terminate(self):
        self._master.destroy()

    def __destroy(self):
        self.callback(Eevent.WindowClose())

    def update(self):
        """Update the Window and Canvas"""
        self._master.update()

    def __bind(self):
        """Sets all the bindings to run through the event callback"""
        self._master.bind("<Key>", event(lambda e: self.callback(Eevent.KeyPress(e.keycode))), add=True)
        self._master.bind("<KeyRelease>", event(lambda e: self.callback(Eevent.KeyRelease(e.keycode))), add=True)

        self._master.bind("<Button>", event(lambda e: self.callback(Eevent.MousePress(e.num, e.x, e.y))), add=True)
        self._master.bind("<ButtonRelease>", event(lambda e: self.callback(Eevent.MouseRelease(e.num, e.x, e.y))), add=True)

        self._master.bind("<FocusIn>", event(lambda e: self.callback(Eevent.WindowFocusGain())), add=True)
        self._master.bind("<FocusOut>", event(lambda e: self.callback(Eevent.WindowFocusLose())), add=True)

        def resize(event):
            self._canvas.configure(width=event.width, height=event.height)
            # print(event.width, event.height, self._canvas.xview(), self._canvas.yview())
            # self._canvas.configure(width=event.width, height=event.height, scrollregion=(-event.width, -event.height, event.width, event.height))
            # self._canvas.xview_moveto(.5)
            # self._canvas.yview_moveto(.5)
            self.callback(Eevent.WindowResize(event.width, event.height))
            # print(self._canvas.xview(), self._canvas.yview(), event.width, event.height)
        self._master.bind("<Configure>", event(resize), add=True)

        self._master.bind("<Motion>", event(lambda e: self.callback(Eevent.MouseMove(e.x, e.y))), add=True)
        self._master.bind("<Destroy>", event(lambda e: self.callback(Eevent.WindowClose())), add=True)

    def title(self, name: str=None) -> str:
        """Sets the Title of the Window
        if None, returns the current name"""
        if name is not None:
            self._master.title(name)
            return name
        return self._master.title

    @property
    def size(self) -> Vector:
        return self.__size
    @property
    def width(self) -> int:
        return self.__size[0]
    @property
    def height(self) -> int:
        return self.__size[1]

    @size.setter
    def size(self, vec: Vector):
        self.__size = vec.int()
        self._canvas.configure(width=self.__size[0], height=self.__size[1])
