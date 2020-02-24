from engine.ecs.system import System
from engine.ecs.world import World

class Script(System):

    def update(self):
        for component in World.active().Data().scripts:
            component.update()