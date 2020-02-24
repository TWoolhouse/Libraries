from collections import defaultdict
from engine.ecs.entity import Entity
from engine.ecs.component import Component
from engine.ecs.parent import Parent
from engine.ecs.transform import Transform

class WorldData:
    def __init__(self):
        self.scripts = set()
        self.event_handles = []

class World:

    _active = None

    def __init__(self, run=True):
        self._entities = {}
        self._components = defaultdict(set)
        self._systems = []
        self._container = WorldData()

        if run:
            self.run()

    def iter_component(self, type) -> [Component]:
        return self._components[type]

    def Data(self) -> WorldData:
        return self._container

    def add_component(self, component):
        self._components[type(component)].add(component)
    def add_entity(self, entity):
        self._entities[entity.id] = entity
    def add_system(self, system):
        self._systems.append(system)

    def update(self):
        for system in self._systems:
            system.update()

    def run(self):
        self.__class__._active = self

    @classmethod
    def active(cls):
        return cls._active

    def Instantiate(self, *components, parent=None, transform=None) -> Entity:
        components = list(components)
        components.insert(0, Transform() if transform is None else transform)
        if parent is not None:
            components.insert(0, Parent(parent))
        for component in components:
            self.add_component(component)
        entity = Entity(*components)
        self.add_entity(entity)
        return entity

def Instantiate(*components, parent=None, transform=None) -> Entity:
    return World.active().Instantiate(*components, parent=parent, transform=transform)