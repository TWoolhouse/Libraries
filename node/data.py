from typing import Union

__all__ = ["Data", "Tag"]

class Tag:
    """Create a Tag"""
    def __init__(self, tag: str):
        """Create a Tag"""
        self.tag = tag

    def __eq__(self, other: Union["Tag", str]):
        if isinstance(other, self.__class__):
            return self.tag == other.tag
        return self.tag == other

    def __hash__(self) -> int:
        return self.tag.__hash__()

    def __repr__(self) -> str:
        return f"T{self.tag}" if self.tag else ""

class Data:
    """Packet to Send over Network"""

    def __init__(self, data: Union[str, bytes], *header: Union[str, Tag]):
        """Packet to Send over Network"""
        self.head = []
        self.tag = []
        self.data = data

        for prefix in header:
            if isinstance(prefix, Tag):
                self.tag.append(prefix)
            else:
                self.head.append(prefix)

    def __repr__(self) -> str:
        return "{}<[{}] ({}) : {}>".format(self.__class__.__name__, "-".join(self.head), ",".join(map(str, self.tag)), self.data)

    def __hash__(self) -> int:
        return id(self)