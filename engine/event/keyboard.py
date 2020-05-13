from engine.event.event import Event
import engine.input.keys

__all__ = ["Key", "KeyPress", "KeyRelease", "KeyRepeat"]

class Key(Event):

    def __init__(self, key: int):
        super().__init__()
        self.key = engine.input.keys.Key(key)

    def __repr__(self) -> str:
        return "{}".format(self.key.name)

class KeyPress(Key):
    def __init__(self, key: int):
        super().__init__(key)
        engine.input.keys._keys[key] = True

class KeyRelease(Key):
    def __init__(self, key: int):
        super().__init__(key)
        engine.input.keys._keys[key] = False

class KeyRepeat(Key):
    def __init__(self, key: int):
        super().__init__(key)
        engine.input.keys._keys[key] = True