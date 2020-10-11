from ..entity import Entity
from ..component import Component
from .render import Render as CRenders
from ...render.text import Text as RText

__all__ = ["FPS"]

class FPS(Component):

    def __init__(self, dp: int=3):
        self.dp = dp

    def initialize(self):
        prim = self.Get(CRenders).primative()
        if isinstance(prim, RText):
            self.text = prim

    def value(self, fps: float):
        self.text.text = round(fps, self.dp)