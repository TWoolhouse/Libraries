from engine.ecs.system import System
from engine.ecs.components.render import Render as CRender

__all__ = ["Render"]

class Render(System):

    def update(self, app):
        if app.render._scene:
            for component in self.components(CRender):
                if component._update or any(i!=j for i,j in zip(component._global_transform, component._u_transform())) or (component._vcache and component._volatile()):
                    component._update = False
                    component._u_drawn_primative()
                app.render.submit(component._drawn)