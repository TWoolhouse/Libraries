import json
import pickle
from typing import Union, Any

__all__ = ["Data", "Tag"]

class Tag:
    """Create a Tag"""
    def __init__(self, tag: str):
        """Create a Tag"""
        self.tag = str(tag)

    def __eq__(self, other: Union["Tag", str]):
        if isinstance(other, self.__class__):
            return self.tag == other.tag
        return self.tag == str(other)

    def __hash__(self) -> int:
        return self.tag.__hash__()

    def __bool__(self):
        return bool(self.tag)

    def __str__(self) -> str:
        return str(self.tag)

    def __repr__(self) -> str:
        return f"T{self.tag}"

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
                self.head.append(prefix.upper())

    def __repr__(self) -> str:
        return "{}<[{}] ({}) : {}>".format(self.__class__.__name__, "-".join(self.head), ",".join(map(str, self.tag)), self.data)

    def __hash__(self) -> int:
        return id(self)

    def _encode(self) -> tuple[str, bytes]:
        if isinstance(self.data, (bytes, bytearray)): # Bytes
            return "BIN", self.data
        elif isinstance(self.data, bool): # Bool
            return "BOOL", b"\x01" if self.data else b"\x00"
        elif isinstance(self.data, int): # Int
            if self.data < 0: # Signed
                return "SINT", self.data.to_bytes((8 + (self.data + (self.data < 0)).bit_length()) // 8, byteorder="big", signed=True)
            return "UINT", self.data.to_bytes((self.data.bit_length() + 7) // 8, byteorder="big", signed=False)
        elif isinstance(self.data, str): # String
            return "STR", self.data.encode("utf8")
        elif isinstance(self.data, (list, dict)): # JSON
            return "JSON", json.dumps(self.data).encode("utf8")
        else: # Pickle
            try:
                return "PKL", pickle.dumps(self.data)
            except pickle.PickleError:
                return "STR", str(self.data).encode("utf8")

    def _decode(self, dtype: str) -> Any:
        if dtype == "BIN": # Bytes
            return self.data
        elif dtype == "STR": # String
            return self.data.decode("utf8")
        elif dtype == "UINT": # Unsigned Int
            return int.from_bytes(self.data, byteorder="big", signed=False)
        elif dtype == "SINT": # Signed Int
            return int.from_bytes(self.data, byteorder="big", signed=True)
        elif dtype == "JSON":
            return json.loads(self.data.decode("utf8"))
        elif dtype == "PKL":
            return pickle.loads(self.data)
        elif dtype == "BOOL":
            return self.data != b"\x00"
