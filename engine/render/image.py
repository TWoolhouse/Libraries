from engine.render.primitive import Primitive
from vector import Vector
from engine.asset.image import Image as ImageAsset

__all__ = ["Image"]

class Image(Primitive):

    def __init__(self, pos: Vector, asset: ImageAsset):
        super().__init__()
        self.pos = pos
        self.asset = asset

    def render(self, canvas):
        canvas.create_image(*self.pos, image=self.asset.render, anchor="nw")

    def Transform(self, translate: Vector=Vector(0, 0), rotation: float=0.0, scale: Vector=Vector(1, 1)):
        return self.__class__(self.pos + translate, self.asset)