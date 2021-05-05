class Singleton(type):
    __instances = {}
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instances[cls]
        except KeyError:
            self = super().__call__(*args, **kwargs)
            cls.__instances[cls] = self
            return self
