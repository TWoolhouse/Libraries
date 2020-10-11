from .deltatime import DeltaTime
from .window import Window
from ..render.render import Render
from .world import World
from ..event.event import Event
from ..event.window import WindowClose
from ..ecs.core.transform import Transform, Component, Entity
from .program import Program
from .settings import Settings

class _Active(type):
    """A metaclass for Application to create a singleton
    We want application to be a singleton most of the time as switching apps will result in strange behaviour
    (Mainly due to the way tk handles having multiple windows, its best to be bound to one instance)
    It is possible to create new Apps through the "new" argument
    """

    __instance = None
    def __call__(cls, *args, new=False, **kwargs):
        """Use new to create a new instance even when one already exists
        Will overwrite the current instance
        """
        if new or cls.__instance is None:
            return super().__call__(*args, **kwargs)
        return cls.__instance

    def activate(cls, obj):
        """Set "obj" as the current active instance"""
        cls.__instance = obj

    def active(cls):
        """Returns the current instance"""
        return cls.__instance

class Application(metaclass=_Active):
    """Application holds referance to all major parts of the program
    It is used to access the current active instance
    It controls the flow of execution
    """

    def __init__(self, program: Program):
        """Takes "program" which allows for code to be executed at initialization and termination of the Application
        The constructor also creates the "World", "Window", the "Render" pipeline and finally, the "Settings"
        These 4 and the "Program" are the core structures of the Application
        """
        self.running = False
        self.world = World()
        self.window = Window(self.event)
        self.render = Render(self.window)
        self.setting = Settings()
        self.program = program

    def initialize(self):
        """Initializes the core structures
        Sets this to be the active instance and sets the "running" flag
        The "program" is initialized before the "world"
        """
        self.__class__.activate(self)
        self.running = True
        self.window.initialize()
        DeltaTime.initialize()
        self.program.initialize(self)
        self.world.initialize()

    def terminate(self):
        """Terminates the core structures
        Runs in the opposite order of the "initialize" method
        The running flag is disabled first
        """
        self.running = False
        self.world.terminate()
        self.program.terminate(self)
        self.window.terminate()
        self.__class__.activate(None)

    def main(self):
        """The main loop of execution
        Runs both initialization and termination as well as required update functions
        Exits on error or "running" flag
        """
        try:
            self.initialize()
            while self.running:
                self.window.update()
                if DeltaTime.update(): # Only render if we have enough time
                    self.render.scene(True)
                self.world.update(self)
                self.render.scene(False)
        finally:
            self.terminate()

    def event(self, event: Event):
        """Top the event stack
        All events propegate from here
        "WindowClose" events will disable the "running" flag, terminating the Application
        """
        if event.dispatch(WindowClose, True):
            self.running = False
        self.world.event(event)

    def transfer(self, world: World) -> World:
        """Swaps the active world
        Returns the current world
        """
        old = self.world
        self.world = world
        return old

def main(application: Application):
    """Main Entry Point
    Will run to "application" termintates
    """
    application.main()

def app() -> Application:
    """Return the Active Application
    Will return "None" if no Application is currently active
    """
    return _Active.active(Application)

def instantiate(*components: Component, parent: Entity=None, transform: Transform=None, id: bool=True) -> Entity:
    """Instantiate a new Entity
    Will instantiate the new Entity into the Applications world
    """
    return app().world.instantiate(*components, parent=parent, transform=transform, id=id)