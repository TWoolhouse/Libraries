from engine.error.base import RenderError

__all__ = ["PrimitiveError", "CanvasError"]

class PrimitiveError(RenderError):

    def __init__(self, primative, msg: str=None):
        super().__init__(msg)
        self.primative = primative

    def __str__(self) -> str:
        return "{} {}".format(self.primative, super().__str__())

class CanvasError(RenderError):

    def __init__(self, canvas, cause: Exception):
        self.canvas = canvas
        self.cause = cause

    def __str__(self) -> str:
        return "{} -> {}: {}".format(self.canvas, self.cause.__class__.__name__, self.cause)