from ..system import System
from ..components.collider import Collider as CCollider
from ...physics import collider
from ...core.application import app as Application
from ..._settings.collider import Setting
import layer

__all__ = ["Collider"]

class Collider(System):

    def __init__(self):
        super().__init__()
        self.setting = Setting()
        Application().setting.collision = lambda: self.setting
        self.sweep_prune = collider.SweepPrune()

    def update(self, application: 'Application'):
        colliders = set(self.components(CCollider))
        for c in colliders:
            c.collision.clear()
        for c1, c2 in self.sweep_prune.detect(self.setting.matrix, colliders):
            if collider.detect(c1, c2):
                c1.collision.add(c2)
                c2.collision.add(c1)
