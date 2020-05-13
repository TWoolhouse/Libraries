from engine.ecs.component import Component

class System:

    def __init__(self):
        pass

    def __call__(self, application):
        self.__app = application
        self.update(application)

    def update(self, application):
        pass

    def components(self, type: Component, *types: Component) -> [Component,]:
        return self.__app.world.components(type, *types)