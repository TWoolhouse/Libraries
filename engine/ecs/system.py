from engine.ecs.world import World

class System:

    def __init__(self):
        pass
    def update(self):
        pass
    def components(self, type, *types):
        if types:
            for component in World.active().iter_component(type):
                yield (component, *(component.Get(t) for t in types))
        else:
            yield from World.active().iter_component(type)