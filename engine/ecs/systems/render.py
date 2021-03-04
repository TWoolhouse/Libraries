from engine.ecs.system import System
from engine.ecs.components.render import Render as CRender
from ..._settings.render import Setting
from ...core.application import app as Application

__all__ = ["Render"]

class Render(System):

    def __init__(self):
        super().__init__()
        self.setting = Setting()
        Application().setting.render = lambda: self.setting

    def update(self, app: 'Application'):
        if app.render._scene:
            for component in self.components(CRender):
                if self.resubmit(component):
                    component._update = False
                    component._u_drawn_primative()
                app.render.submit(component._drawn)

    def resubmit(self, component: CRender) -> bool:
        return component._update or \
            any(i!=j for i,j in zip(component._global_transform, component._u_transform())) or \
            (component._vol and component._volatile())
