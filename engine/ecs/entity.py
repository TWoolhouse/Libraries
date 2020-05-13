import engine.error
from engine.ecs.component import Component

__all__ = ["Entity"]

class Entity:

    def __init__(self, *components: Component, id: int=0):
        self._components = components
        self._component_types = {type(c) : c for c in self._components}
        self.id = id

    def Get(self, component: Component) -> Component:
        try:
            return self._component_types[component]
        except KeyError:
            raise engine.error.ecs.GetComponentError(self, component) from None

    def initialize(self) -> bool:
        for component in self._components:
            if component._running:
                continue
            component.entity = self
            if res := component.initialize():
                raise engine.error.ecs.InitializeComponent(self, component, res)
            component._running = True
        return True

    def terminate(self) -> bool:
        for component in self._components:
            if res := component.terminate():
                raise engine.error.ecs.TerminateComponent(self, component, res)
            component._running = False
        return True

    def __repr__(self) -> str:
        pid = f"{pid.id if (pid:=self._components[0].parent(False)) else ''}"
        return "{}[{}]<{}>".format(self.__class__.__name__, self.id, ", ".join(filter(None, (pid, *(c.__class__.__name__ for c in self._components[2:])))))