from engine.ecs.system import System
from engine.ecs.components.render import Render as CRender
from ..._settings.render import Setting
import layer
from ...core.application import app as Application

__all__ = ["Render"]

def rerender(component: CRender) -> bool:
    if require_rerender(component):
        component._update = False
        component._u_drawn_primative()
        return True
    return False

def require_rerender(component: CRender) -> bool:
    return component._update or \
        any(i!=j for i,j in zip(component._global_transform, component._u_transform())) or \
        (component._vol and component._volatile())

class RenderStackData(layer.Data):

    def __init__(self, type: layer.Type.Item, active: bool):
        super().__init__(type, self.__call__, active)
        self.bucket: list[CRender] = []

    def __call__(self, app: 'Application'):
        for component in self.bucket:
            app.render.submit(component._drawn)
        self.bucket.clear()

class Render(System):

    def __init__(self):
        super().__init__()
        self.setting = Setting()
        Application().setting.render = lambda: self.setting
        self.setting._stack_data = RenderStackData
        self.setting.compile()

    def update(self, app: 'Application'):
        if app.render._scene:
            for component in self.components(CRender):
                rerender(component)
                self.setting.stack[component.layer].bucket.append(component)
        self.setting.stack(app)
