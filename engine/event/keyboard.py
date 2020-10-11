from .event import Event
from ..input import keys as ikeys

__all__ = ["Key", "KeyPress", "KeyRelease", "KeyRepeat"]

class Key(Event):

    def __init__(self, key: int):
        super().__init__()
        self.key = ikeys.Key(key)

    def __repr__(self) -> str:
        return "{}".format(self.key.name)

class KeyPress(Key):
    def __init__(self, key: int):
        super().__init__(key)
        ikeys._keys[key] = True

class KeyRelease(Key):
    def __init__(self, key: int):
        super().__init__(key)
        ikeys._keys[key] = False

class KeyRepeat(Key):
    def __init__(self, key: int):
        super().__init__(key)
        ikeys._keys[key] = True