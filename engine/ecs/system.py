from .component import Component
from typing import Type, TypeVar, Iterator, overload

C = TypeVar("C", bound=Component)

class System:

    def __init__(self):
        pass

    def __call__(self, application: 'Application'):
        self.__app = application
        self.update(application)

    def update(self, application: 'Application'):
        pass

    @overload
    def components(self, type: Type[C]) -> Iterator[C]: ...
    @overload
    def components(self, type: Type[C], *types: Type[C]) -> Iterator[tuple[C]]: ...

    def components(self, type: Type[C], *types: Type[C]) -> Iterator[C]:
        return self.__app.world.components(type, *types)
