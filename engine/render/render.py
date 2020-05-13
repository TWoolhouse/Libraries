from engine.render.primitive import Primitive

__all__ = ["Render"]

class Render:

    def __init__(self, window):
        self._scene = False
        self._objects = set()
        self._window = window

    def scene(self, flag: bool=None):
        if self._scene:
            for obj in tuple(self._objects):
                if obj._rendered:
                    obj._rendered = False
                else:
                    self._window.canvas.delete(obj._widget)
                    obj._widget = None
                    self._objects.remove(obj)
        self._scene = not self._scene if flag is None else flag

    def submit(self, obj: Primitive):
        obj._rendered = True
        if obj._widget is None and self._scene:
            obj._widget = obj.render(self._window.canvas)
            self._objects.add(obj)