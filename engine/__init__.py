import sys
from vector import Vector
import engine.core
from engine.core import layer
import engine.event
import engine.input
import engine.render
import engine.ecs
import engine.component
import engine.ecs.systems
import engine.physics
from engine.core.application import main, app, instantiate

class __Module(sys.modules[__name__].__class__):
    def __call__(self) -> engine.core.Application:
        return app()

sys.modules[__name__].__class__ = __Module

__all__ = [
"Vector",
"main", "app", "instantiate",
"core", "layer", "event", "input", "render", "ecs", "component",
]
