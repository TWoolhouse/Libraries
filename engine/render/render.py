from engine.core.single import Singleton
from engine.render.primitive import Primitive

__all__ = ["Render"]

class Render(metaclass=Singleton):

    def __init__(self, window):
        self._objects = set()
        self._scene = False
        self._window = window

    def scene(self):
        if self._scene: # End Scene
            # print("END")
            for obj in tuple(self._objects):
                if obj._rendered:
                    obj._rendered = False
                else:# elif obj._widget is not None:
                    self._window.canvas.delete(obj._widget)
                    obj._widget = None
                    self._objects.remove(obj)
                    # print("DELETE", obj)
        else: # Begin Scene
            pass
            # print("STart")
        self._scene = not self._scene

    def submit(self, obj: Primitive):
        obj.render(self)