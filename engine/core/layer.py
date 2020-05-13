import enum
from collections import defaultdict

__all__ = ["Type", "Data", "Mask", "Stack"]

class Type:

    @staticmethod
    def new(name: str, *types: str, **vtypes: {str, int}) -> type(enum.IntEnum):
        return enum.unique(enum.IntEnum(name, {"NONE":0, **{t:i for i,t in enumerate(types, start=1)}, **vtypes}))

    @staticmethod
    def add(types: type(enum.IntEnum), name: str, value: int=0):
        if value == 0:
            value = list(types)[-1].value
        setattr(types, name, value)

    @staticmethod
    def move(type: enum.IntEnum, value: int):
        raise NotImplementedError
        type.value = value

class Data:

    def __init__(self, type: Type, func: callable, active: bool=True):
        self.type = type
        self.func = func
        self.active = active

    def __call__(self, *args, **kwargs) -> object:
        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        try:
            name = self.func.__qualname__
        except AttributeError:
            name = self.func
        return f"LayerData<{self.type.name}-{self.active} Func:{name}>"

class Mask:

    def __init__(self, *types: Type, invert: bool=False):
        self.types = types
        self.invert = invert

    def __repr__(self) -> str:
        return "LayerMask<{}>".format(", ".join(i.name for i in self.types))

class Stack:

    def __init__(self, type: Type, *layers: Data, mask: Mask=None):
        self.type = type
        self.layers = defaultdict(list)
        self.stack = []
        self._mask = self.mask(mask)

        for layer in layers:
            self.layers[layer.type].append(layer)

    def mask(self, mask: Mask=None) -> Mask:
        if mask is None:
            self._mask = Mask(self.type.NONE, invert=True)
        else:
            self._mask = mask
        return self._mask

    def add(self, layer: Data) -> Data:
        self.layers[layer.type].append(layer)
        return layer
    def remove(self, layer: Data) -> Data:
        self.layers[layer.type].remove(layer)
        return layer

    def compile(self, mask: Mask=True):
        self.stack.clear()
        if mask != True:
            self.mask(mask)
        for t in self.type:
            if (t in self._mask.types) != self._mask.invert:
                for layer in self.layers[t]:
                    if layer.active:
                        self.stack.append(layer)

    def activate(self, layer: Data, flag: bool=None) -> bool:
        if flag is None:
            layer.active = not layer.active
        else:
            layer.active = flag
        return layer.active

    def __call__(self, *args, **kwargs):
        for layer in self.stack:
            layer(*args, **kwargs)

    def __iter__(self) -> iter:
        return self.stack.__iter__()

    def __repr__(self) -> str:
        return "LayerStack<{}[{}] {}>".format(self.type.__name__, len(self.stack), ", ".join(f"{k.name}:{len(v)}" for k,v in self.layers.items()))