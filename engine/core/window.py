import tkinter as tk
import engine.event

__all__ = ["Window"]

def event(func):
    def event_binding(event):
        func(event)
        return "break"
    return event_binding

class Window:

    def __init__(self, callback: callable):
        self.callback = callback
        self._master = tk.Tk()
        self._master.protocol("WM_DELETE_WINDOW", self._destroy)
        self.canvas = tk.Canvas(self._master, width=1280, height=720, bd=-2)
        self.canvas.pack()
        self.bind()

    def initialize(self):
        self.canvas.focus_force()

    def terminate(self):
        self._master.destroy()

    def _destroy(self):
        self.callback(engine.event.WindowClose())

    def update(self):
        self._master.update()

    def bind(self):
        self._master.bind("<Key>", event(lambda e: self.callback(engine.event.KeyPress(e.keycode))), add=True)
        self._master.bind("<KeyRelease>", event(lambda e: self.callback(engine.event.KeyRelease(e.keycode))), add=True)

        self._master.bind("<Button>", event(lambda e: self.callback(engine.event.MousePress(e.num, e.x, e.y))), add=True)
        self._master.bind("<ButtonRelease>", event(lambda e: self.callback(engine.event.MouseRelease(e.num, e.x, e.y))), add=True)

        self._master.bind("<FocusIn>", event(lambda e: self.callback(engine.event.WindowFocusGain())), add=True)
        self._master.bind("<FocusOut>", event(lambda e: self.callback(engine.event.WindowFocusLose())), add=True)

        def resize(event):
            self.canvas.configure(width=event.width, height=event.height)
            self.callback(engine.event.WindowResize(event.width, event.height))
        self._master.bind("<Configure>", event(resize), add=True)

        self._master.bind("<Motion>", event(lambda e: self.callback(engine.event.MouseMove(e.x, e.y))), add=True)
        self._master.bind("<Destroy>", event(lambda e: self.callback(engine.event.WindowClose())), add=True)
