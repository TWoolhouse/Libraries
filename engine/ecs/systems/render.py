from engine.ecs.system import System
from engine.ecs.components import Render as CRender
import engine.render

class Render(System):

    def update(self):
        for component in self.components(CRender):
            if component.update or any((i != j for i,j in zip(component._render_transform, (component.transform.position_global, component.transform.rotation_global, component.transform.scale_global)))):
                component.update_primative()
            engine.render.Render().submit(component.primative)