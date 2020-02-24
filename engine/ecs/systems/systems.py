from engine.ecs.base_ecs import System, Component
from engine.ecs import components
from engine.ecs import event

class RenderPrimative(System):

    type = components.Graphic

class Collision(System):

    type = components.Collider

    # def update(self):
    #     for component in self.components:
    #         pass

    def component(self, component: components.Collider):
        for other in self.components:
            if value := component.collider.detect(component.transform, other, other.transform):
                component.event(event.Collision(value))
        component.flag = False