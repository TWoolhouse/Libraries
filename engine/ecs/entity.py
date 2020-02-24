import engine.error

class Entity:

    def __init__(self, *components):
        self._components = components
        self._component_types = {type(c) : c for c in self._components}
        self.id = 10

        for component in self._components:
            component._entity = self
            if not component.initialize():
                raise engine.error.EntityComponentError(self, component, "Failed to Initialize!")

    def component(self, type):
        try:
            return self._component_types[type]
        except KeyError:
            raise engine.error.EntityComponentGetError(self, type)
    def __getitem__(self, key):
        return self.component(key)

    def terminate(self):
        for component in self._components:
            if not component.terminate():
                raise engine.error.EntityComponentError(self, component, "Failed to Terminate!")

    def __del__(self):
        self.terminate()

    def __repr__(self) -> str:
        return "Entity{}<{}>".format(self.id, ", ".join((i.__name__ for i in self._component_types.keys())))