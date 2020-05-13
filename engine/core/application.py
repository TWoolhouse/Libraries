from engine.core.deltatime import DeltaTime
from engine.core.window import Window
from engine.render.render import Render
from engine.core.world import World
from engine.event.event import Event
from engine.event.window import WindowClose
from engine.ecs.core.transform import Transform, Component, Entity
from engine.core.program import Program
from engine.core.settings import Settings

class _Active(type):

    __instance = None
    def __call__(cls, *args, new=False, **kwargs):
        if new or cls.__instance is None:
            return super().__call__(*args, **kwargs)
        return cls.__instance

    def activate(cls, obj):
        cls.__instance = obj

    def active(cls):
        return cls.__instance

class Application(metaclass=_Active):

    def __init__(self, program: Program):
        self.running = False
        self.world = World()
        self.window = Window(self.event)
        self.render = Render(self.window)
        self.setting = Settings()
        self.program = program

    def initialize(self):
        self.__class__.activate(self)
        self.running = True
        self.window.initialize()
        DeltaTime.initialize()
        self.program.initialize(self)
        self.world.initialize()

    def terminate(self):
        self.running = False
        self.world.terminate()
        self.program.terminate(self)
        self.window.terminate()
        self.__class__.activate(None)

    def main(self):
        self.initialize()
        while self.running:
            self.window.update()
            if DeltaTime.update():
                self.render.scene(True)
            self.world.update(self)
            self.render.scene(False)
        self.terminate()

    def event(self, event: Event):
        if event.dispatch(WindowClose, True):
            self.running = False
        self.world.event(event)

def main(application: Application):
    application.main()

def app() -> Application:
    return _Active.active(Application)

def instantiate(*components: Component, parent: Entity=None, transform: Transform=Transform(), id: bool=True) -> Entity:
    return app().world.instantiate(*components, parent=parent, transform=transform, id=id)