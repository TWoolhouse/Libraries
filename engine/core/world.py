from collections import defaultdict
import random

import engine.error
from engine.core import layer
from engine.event.event import Event

from engine.ecs.core.parent import Parent, Component, Entity
from engine.ecs.core.transform import Transform

ENTITY_LIMIT = 2 ** 8
# 255 Limit
# 0 is reserved for:
# Null entities
# Children within components

class World:

    def __init__(self):
        __layer_type__system = layer.Type.new("SystemLayer", PRE=10, SCRIPT=20, PHYSICS=30, RENDER=40, POST=50)
        __layer_type__event = layer.Type.new("EventLayer", WINDOW=10, UI=20, CONTROL=30)

        self._entities_null = set()
        self._entities = {}
        self._components = defaultdict(set)
        self.systems = layer.Stack(__layer_type__system)

        self._script_components = set()
        self.events = layer.Stack(__layer_type__event)

    def initialize(self):
        for entity in self._entities.values():
            entity.initialize()
        for entity in self._entities_null:
            entity.initialize()

        self.systems.compile(layer.Mask(self.systems.type.NONE, invert=True))
        self.events.compile(layer.Mask(self.events.type.NONE, invert=True))
    def terminate(self):
        self.systems.compile(layer.Mask(self.systems.type.NONE))
        self.events.compile(layer.Mask(self.events.type.NONE))

        for entity in self._entities_null:
            entity.terminate()
        for entity in self._entities.values():
            entity.terminate()

    def update(self, application):
        self.systems(application)
    def event(self, event: Event):
        self.events(event)

    def add_system(self, system: "System", type: str="SCRIPT") -> "System":
        self.systems.add(layer.Data(getattr(self.systems.type, type), system))
        return system

    def system(self, system: "System", flag: bool=None) -> bool:
        for layers in self.systems.layers.values():
            for layer in layers:
                if isinstance(layer.func, system):
                    return self.systems.activate(layer, flag)

    def components(self, type_: "Component", *types: "Component") -> ["Component",]:
        if types:
            for component in self._components[type_]:
                try:
                    yield (component, *map(component.Get, types))
                except engine.error.ecs.GetComponentError: continue
        else:
            yield from self._components[type_]

    def instantiate(self, *components: Component, parent: Entity=None, transform: Transform=Transform(), id: bool=True) -> Entity:
        parent = Parent(parent)
        if id:
            while len(self._entities) < ENTITY_LIMIT-1:
                idv = random.randint(1, ENTITY_LIMIT)
                if idv not in self._entities:
                    break
            ent = Entity(parent, transform, *components, id=idv)
            self._entities[idv] = ent
        else:
            ent = Entity(parent, transform, *components)
            self._entities_null.add(ent)
        for component in ent._components:
            self._components[type(component)].add(component)
        ent.initialize()
        return ent

    def destroy(self, entity: Entity):
        if entity.id == 0:
            self._entities_null.discard(entity)
        else:
            del self._entities[entity.id]

        for component in entity._components:
            self._components[type(component)].discard(component)

        entity.terminate()