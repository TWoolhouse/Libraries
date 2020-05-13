from engine.ecs.system import System
from engine.ecs.components.fps_counter import FPS as CFPS

from collections import deque
from engine.core.deltatime import DeltaTime

__all__ = ["FPS"]

class FPS(System):

    def __init__(self, buffer: int=10):
        self.size = buffer
        self.buffer = deque(maxlen=self.size)
        self.fps = 0

    def update(self, app):
        self.buffer.append(DeltaTime.dt())
        try:
            self.fps = 1 / (sum(self.buffer) / self.size)
        except ZeroDivisionError: pass
        for component in self.components(CFPS):
            component.value(self.fps)