__all__ = ["Data", "Tag"]

class Tag:

    def __init__(self, tag):
        self.tag = tag

class Data:

    def __init__(self, data: (str, bytes), *prefixes: str):
        self.prefixes = []
        self.tags = []
        for header in prefixes:
            if isinstance(header, Tag):
                self.tags.append(str(header.tag).upper())
            else:
                self.prefixes.append(str(header).upper())
        self.data = data

    def __repr__(self) -> str:
        return "<{} [{}] ({}) : {}>".format(self.__class__.__name__, "-".join(self.prefixes), ",".join(self.tags), self.data)
