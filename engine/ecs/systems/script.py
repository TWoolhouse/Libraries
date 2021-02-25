from ..system import System

__all__ = ["Script"]

class Script(System):

    def update(self, app: 'Application'):
        for component in app.world._script_components:
            component.update()
