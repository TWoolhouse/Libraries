__all__ = ["Data"]

class Data:

    def __init__(self, data: (str, bytes), *prefixes: str, tags: str=()):
        self.prefixes = [str(i).upper() for i in prefixes]
        self.tags = [str(i) for i in prefixes]
        self.data = data
