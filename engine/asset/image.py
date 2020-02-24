from engine.asset.base_asset import Asset
import PIL.Image, PIL.ImageTk

class Image(Asset):

    def __init__(self, path: str):
        self._path = path
        self._image = PIL.Image.open(self._path)
        self._tkimage = PIL.ImageTk.PhotoImage(self._image)

    @property
    def image(self):
        return self._image

    @property
    def render(self):
        return self._tkimage