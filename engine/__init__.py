import sys
from vector import Vector
from . import core
from .core import layer
from . import event
from . import input
from . import render
from . import ecs
from . import component
from . import physics
from .core.application import main, app, instantiate

class __Module(sys.modules[__name__].__class__):
    # Do janky things
    # Init the systems module so its already imported
    from .ecs import systems
    # Add Application to render.text module so Font is able to access the current App
    setattr(render.text, "Application", app)

    # Calls to "engine()" is "engine.app()"
    def __call__(self) -> core.Application:
        return app()

sys.modules[__name__].__class__ = __Module

__all__ = [
"Vector",
"main", "app", "instantiate",
"core", "layer", "event", "input", "render", "ecs", "component",
]
