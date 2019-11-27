__all__ = ["Data"]

class Data:

    def __init__(self, data: (str, bytes), *prefixes: str, tags: str=()):
        self.prefixes = [str(i).upper() for i in prefixes]
        self.tags = [str(i) for i in tags]
        self.data = data

    def __repr__(self) -> str:
        return "<{} [{}] ({}) : {}>".format(self.__class__.__name__, "-".join(self.prefixes), ",".join(self.tags), self.data)