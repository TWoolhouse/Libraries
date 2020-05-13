from engine.ecs.system import System
from engine.ecs.components.collider import Collider as CCollider
from engine.physics import collider
from engine.core.application import app as Application
from engine.core import layer
from engine._settings.collider import Setting

__all__ = ["Collider"]

class Collider(System):

    def __init__(self):
        self.setting = Setting()
        Application().setting.collision = self.get_settings

    def get_settings(self) -> Setting:
        return self.setting

    def update(self, application):
        colliders = set(self.components(CCollider))
        for c in colliders:
            c.collision.clear()
        for component in colliders:
            mask = {j for i in component.layers for j in self.setting.matrix[i]}
            for other in (c for c in colliders if not ((component in c.collision or c is component) or mask.isdisjoint(c.layers))):
                if collider.detect(component, other):
                    component.collision.add(other)
                    other.collision.add(component)
