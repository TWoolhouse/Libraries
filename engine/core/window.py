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
        self.canvas = tk.Canvas(width=1280, height=720, bd=-2)
        self.canvas.pack()
        self.canvas.focus()
        self.canvas.master.protocol("WM_DELETE_WINDOW", self._destroy)
        self.bind()

    def destroy(self):
        self.canvas.master.destroy()

    def _destroy(self):
        self.callback(engine.event.WindowClose())
        # self.canvas.master.destroy()

    def __del__(self):
        self.destroy()

    def update(self):
        self.canvas.update()

    def bind(self):
        self.canvas.master.bind("<Key>", event(lambda e: self.callback(engine.event.KeyPress(e.keycode))), add=True)
        self.canvas.master.bind("<KeyRelease>", event(lambda e: self.callback(engine.event.KeyRelease(e.keycode))), add=True)

        self.canvas.master.bind("<Button>", event(lambda e: self.callback(engine.event.MousePress(e.num, e.x, e.y))), add=True)
        self.canvas.master.bind("<ButtonRelease>", event(lambda e: self.callback(engine.event.MouseRelease(e.num, e.x, e.y))), add=True)

        self.canvas.master.bind("<FocusIn>", event(lambda e: self.callback(engine.event.WindowFocusGain())), add=True)
        self.canvas.master.bind("<FocusOut>", event(lambda e: self.callback(engine.event.WindowFocusLose())), add=True)

        def resize(event):
            self.canvas.configure(width=event.width, height=event.height)
            self.callback(engine.event.WindowResize(event.width, event.height))
        self.canvas.master.bind("<Configure>", event(resize), add=True)

        self.canvas.master.bind("<Motion>", event(lambda e: self.callback(engine.event.MouseMove(e.x, e.y))), add=True)
        self.canvas.master.bind("<Destroy>", event(lambda e: self.callback(engine.event.WindowClose())), add=True)
