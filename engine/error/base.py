__all__ = ["EngineError", "CoreError", "RenderError", "EventError", "ECSError"]

class EngineError(Exception):

    def __init__(self, msg="Engine Error"):
        self.msg = msg

    def __str__(self) -> str:
        return "Error" if self.msg is None else self.msg.__str__()

class CoreError(EngineError):
    pass
class RenderError(EngineError):
    pass
class EventError(EngineError):
    pass
class ECSError(EngineError):
    pass