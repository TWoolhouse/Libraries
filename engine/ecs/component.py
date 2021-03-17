from typing import Callable, TypeVar

__all__ = ["Component"]

class Component:

    entity = None
    _running = False
    _required_components: set['Component'] = set()

    def __init__(self, entity: 'Entity'=None):
        self.entity: 'Entity' = entity

    def Get(self, component: 'Component') -> 'Component':
        return self.entity.Get(component)

    def initialize(self) -> bool:
        return None
    def terminate(self) -> bool:
        return None

    def __hash__(self) -> int:
        return id(self)
    def __repr__(self) -> str:
        return "Component[{}]".format(self.__class__.__name__)

C = TypeVar("C", bound=Component)

def require(*components: Component) -> Callable[[C], C]:
    def require_components(comp_class: C) -> C:
        for c in components:
            if not issubclass(c, Component):
                raise TypeError
        comp_class._required_components = set(components)
        return comp_class
    return require_components
