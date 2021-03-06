from .. import error
from .component import Component

__all__ = ["Entity"]

class Entity:

    def __init__(self, *components: Component, id: int=0):
        self._components = components
        self._component_types: dict[type[Component], Component] = {type(c) : c for c in self._components}
        if missing := set().union(*(c._required_components for c in self._components)).difference(*(c.mro() for c in self._component_types)):
            raise TypeError
        self.id = id

    def Get(self, component: Component) -> Component:
        try:
            return self._component_types[component]
        except KeyError:
            raise error.ecs.GetComponentError(self, component) from None

    def initialize(self) -> bool:
        for component in self._components:
            if component._running:
                continue
            component.entity = self
            try:
                if res := component.initialize():
                    raise error.ecs.InitializeComponent(self, component, res)
                component._running = True
            except Exception as e:
                raise error.ecs.InitializeComponent(self, component, e) from e
        return True

    def terminate(self) -> bool:
        for component in self._components:
            if component._running:
                try:
                    res = component.terminate()
                except Exception as e:
                    raise error.ecs.TerminateComponent(self, component, e) from e
                finally:
                    component._running = False
                if res:
                    raise error.ecs.TerminateComponent(self, component, res)
        return True

    def __repr__(self) -> str:
        pid = f"{pid.id if (pid:=self._components[0].parent(False)) else ''}"
        return "{}[{}]<{}>".format(self.__class__.__name__, self.id, ", ".join(filter(None, (pid, *(c.__class__.__name__ for c in self._components[2:])))))
