class Singleton(type):

    __instances = {}
    def __call__(cls, *args, **kwargs):
        if cls in cls.__instances:
            return cls.__instances[cls]
        self = super().__call__(*args, **kwargs)
        cls.__instances[cls] = self
        return self

class SingleInit(Singleton):

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls()