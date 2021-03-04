from .component import Component
from typing import Iterator

class System:

    def __init__(self):
        pass

    def __call__(self, application: 'Application'):
        self.__app = application
        self.update(application)

    def update(self, application: 'Application'):
        pass

    def components(self, type: Component, *types: Component) -> Iterator[Component]:
        return self.__app.world.components(type, *types)
