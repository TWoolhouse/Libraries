__all__ = ["Component"]

class Component:

    _running = False
    entity = None

    def __init__(self, entity: 'Entity'=None):
        self.entity = entity

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
