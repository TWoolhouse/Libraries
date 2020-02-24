import engine.error

class Component:

    def __init__(self):
        self._entity = None

    def initialize(self) -> bool:
        return True
    def terminate(self) -> bool:
        return True

    def Get(self, type):
        return self._entity.component(type)
    def Check(self, type):
        try:
            return self._entity.component(type)
        except engine.error.EntityComponentGetError:
            return None

    def __repr__(self) -> str:
        string = self.__str__()
        if string:
            return "Component<{}: {}>".format(self.__class__.__name__, string)
        return "Component<{}>".format(self.__class__.__name__)
    def __str__(self) -> str:
        return ""