from vector import Vector

class _Primitive(type):

    def __new__(cls, name, bases, dct):
        if "render" in dct:
            def wrap(func):
                def render(self, render):
                    self._rendered = True
                    if self._widget is None:
                        self._widget = func(self, render._window.canvas)
                        render._objects.add(self)
                        return self._widget
                return render
            dct["render"] = wrap(dct["render"])
        return super().__new__(cls, name, bases, dct)

class Primitive(metaclass=_Primitive):

    def __init__(self):
        self._widget = None
        self._rendered = False

    def __hash__(self) -> int:
        return id(self)

    def render(self, canvas):
        raise TypeError("'{}' can not be Rendered".format(self.__class__.__name__)) from None

    def Transform(self, translate: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        raise TypeError("'{}' can not Transform".format(self.__class__.__name__)) from None