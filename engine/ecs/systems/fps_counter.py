from ..system import System
from ..components.fps_counter import FPS as CFPS

from collections import deque
from ...core.deltatime import DeltaTime

__all__ = ["FPS"]

class FPS(System):

    def __init__(self, buffer: int=10):
        self.size = buffer
        self.buffer: deque[float] = deque(maxlen=self.size)
        self.fps: float = 0.0

    def update(self, app: 'Application'):
        self.buffer.append(DeltaTime.dt())
        try:
            self.fps = 1 / (sum(self.buffer) / self.size)
        except ZeroDivisionError: pass
        for component in self.components(CFPS):
            component.value(self.fps)
