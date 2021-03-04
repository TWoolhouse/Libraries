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

class SettingError(EngineError):

    def __init__(self, setting: str, msg: str):
        super().__init__(msg)
        self.setting = setting

    def __str__(self) -> str:
        return f"{self.setting} {super().__str__()}"
