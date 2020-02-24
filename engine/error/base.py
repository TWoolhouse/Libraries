__all__ = []

class MetaEngineError(type):

    def __new__(cls, name, bases, dct):
        if "__str__" in dct:
            def wrap(func):
                def _str_(self):
                    s = func(self)
                    return "{}{}".format("", "{}".format(s) if s else "") # self.__class__.__name__
                return _str_
            dct["__str__"] = wrap(dct["__str__"])
        return super().__new__(cls, name, bases, dct)

class BaseEngineException(Exception, metaclass=MetaEngineError):

    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self) -> str:
        return self.msg.__str__()
    def __repr__(self) -> str:
        return self.__str__()

    def _log(self):
        _string = "{}\n\t".format(self)
        _string += self._log_()
        return _string

    def _log_(self):
        _string = ""
        if self.__cause__:
            if isinstance(self.__cause__, BaseEngineException):
                _string += "{}\n\t".format(self.__cause__._log_())
            else:
                _string += "Line[{}:{}] {}: {}\n\t".format(self.__cause__.__traceback__.tb_lineno, self.__cause__.__traceback__.tb_frame.f_code.co_name, self.__cause__.__class__.__name__, self.__cause__)
        _string += "Line[{}:{}] {}".format(self.__traceback__.tb_lineno, self.__cause__.__traceback__.tb_frame.f_code.co_name, self)
        return _string

class FatalError(BaseEngineException):
    pass

class RenderError(BaseEngineException):

    def __init__(self, renderer):
        self.renderer = renderer

    def __str__(self) -> str:
        return "{}".format(self.renderer)

class EventError(BaseEngineException):
    pass

class EntityError(BaseEngineException):

    def __init__(self, entity, msg=""):
        self.entity = entity
        self.msg = msg

    def __str__(self) -> str:
        return "{} -> {}".format(self.entity, self.msg)