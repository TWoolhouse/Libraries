from .primitive import Primitive
from vector import Vector
import tkinter.font as tkf
from .colour import Colour

__all__ = ["Text", "Font"]

class Font:

    __instances = {}
    def __init__(self, size: int=None, family: str=None, name=None):
        if name in self.__instances:
            self.__tkfont = tkf.Font(root=Application().window._canvas, name=name, exists=True)
        else:
            self.__tkfont = tkf.Font(root=Application().window._canvas, family=family, size=size, name=name, exists=False)
            self.__instances[self.__tkfont.name] = self

    @classmethod
    def Get(self, name: str) -> 'Font':
        return self.__instances[name]

    @property
    def name(self) -> str:
        return self.__tkfont.name

    def _font(self) -> tkf.Font:
        return self.__tkfont

    def size(self, value: int=None):
        if value is not None:
            self.__tkfont.config(size=value)
        return self.__tkfont.cget("size")

class Text(Primitive):
    def __init__(self, string: str, font: Font=None, col=Colour(0, 0, 0)):
        super().__init__()
        self.pos = Vector(0, 0)
        self.text = string
        self.colour = col
        self.font = font if isinstance(font, (Font, type(None))) else Font.Get(font)

    def render(self, canvas):
        return canvas.create_text(*self.pos, text=self.text, font=self.font._font() if self.font else None, fill=self.colour.fmt())

    def Transform(self, translate: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        new = self.__class__(self.text, self.font, self.colour)
        new.pos = self.pos.rotate(rotation).map(scale) + translate
        return new

    def _volatile(self, other) -> bool:
        return self.text, self.pos, self.colour, self.font.name

    def __repr__(self) -> str:
        return self.text
