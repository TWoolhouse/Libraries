from .primitive import Primitive

__all__ = ["Render"]

class Render:

    def __init__(self, window):
        self._scene = False
        self.__objects: set[Primitive] = set()
        self.__window = window

    def scene(self, flag: bool=None):
        if self._scene:
            for obj in tuple(self.__objects):
                if obj._rendered:
                    obj._rendered = False
                else:
                    self.__window._canvas.delete(obj._widget)
                    obj._widget = None
                    self.__objects.remove(obj)
        self._scene = not self._scene if flag is None else flag

    def submit(self, obj: Primitive):
        obj._rendered = True
        if obj._widget is None and self._scene:
            obj._widget = obj.render(self.__window._canvas)
            self.__objects.add(obj)
