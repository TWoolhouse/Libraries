__all__ = ["Asset"]

class _Asset(type):

    __instances = {}
    def __call__(cls, name, *args, **kwargs):
        try:
            return cls.__instances[cls][name]
        except KeyError:    pass
        if cls not in cls.__instances:
            cls.__instances[cls] = {}
        self = cls.__instances[cls][name] = super().__call__(*args, **kwargs)
        return self

class Asset(metaclass=_Asset):
    pass