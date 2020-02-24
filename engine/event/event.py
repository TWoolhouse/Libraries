__all__ = ["Event"]

class _Event(type):

    def __new__(cls, name, bases, dct):
        if "__repr__" in dct:
            def wrap(func):
                def __repr__(self) -> str:
                    return "<Event: {} {}>".format(self.__class__.__name__, func(self))
                return __repr__
            dct["__repr__"] = wrap(dct["__repr__"])
        return super().__new__(cls, name, bases, dct)

class Event(metaclass=_Event):
    
    def __init__(self):
        self.handled = False

    def __repr__(self):
        return ""

    def dispatch(self, event, func):
        if isinstance(func, bool):
            if isinstance(self, event):
                self.handled = func
                return True
            return False
        if isinstance(self, event):
            self.handled = func(self)
        return self.handled