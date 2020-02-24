from engine.ecs.component import Component
from engine.ecs.components import Transform
from engine.ecs.world import World

class Script(Component):

    def __init__(self):
        super().__init__()
        World.active().Data().scripts.add(self)

    # def initialize(self) -> bool:
    #     return True

    def update(self):
        pass

    def terminate(self):
        World.active().Data().scripts.add(self)
        return True