from engine.ecs.entity import Entity
from engine.ecs.component import Component

class Parent(Component):
    def __init__(self, entity: Entity):
        self.entity = entity