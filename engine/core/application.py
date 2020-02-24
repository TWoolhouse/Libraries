from engine.core.single import Singleton
from engine.core.deltatime import DeltaTime
from engine.core.layer import LayerStack
from engine.core.window import Window
import engine.event
from engine.event.event import Event
from engine.render.render import Render

class Application(metaclass=Singleton):

    def __init__(self):
        self.running = True
        self.delta_time = DeltaTime()
        self.layer_stack = LayerStack()
        self.window = Window(self.event)
        self.render = Render(self.window)
        self.window.bind()
        
        self.delta_time.next()

    def update(self):
        self.window.update()
        self.delta_time.next()
        self.render.scene()
        self.layer_stack.update()
        self.render.scene()

    def event(self, event: Event):
        if event.dispatch(engine.event.WindowClose, True):
            self.running = False
        self.layer_stack.event(event)