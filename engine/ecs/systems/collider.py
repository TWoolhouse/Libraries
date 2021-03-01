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

    def update(self, application: 'Application'):
        colliders = set(self.components(CCollider))
        for c in colliders:
            c.collision.clear()
        # for component in colliders:
        #     mask = {j for i in component.layers for j in self.setting.matrix[i]}
        #     for other in (c for c in colliders if not ((component in c.collision or c is component) or mask.isdisjoint(c.layers))):
        #         if collider.detect(component, other):
        #             component.collision.add(other)
        #             other.collision.add(component)
