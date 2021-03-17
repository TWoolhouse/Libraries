import layer
from typing import Callable

class Setting:
    def __init__(self):
        self.layers = layer.Type("RenderLayer", Main=100, UI=200)
        self.stack = layer.StackQ(self.layers)
        self._stack_data: Callable[[layer.Type.Item, bool], layer.Data] = lambda t,b: layer.Data(t, lambda: None, b)

    def compile(self, mask: layer.Mask=True) -> layer.StackQ:
        for ltype in set(self.stack.layers).difference(self.layers):
            self.stack.remove(ltype)
        for ltype in set(self.layers).difference(self.stack.layers):
            self.stack.add(self._stack_data(ltype, True))
        self.stack.compile(mask)
        return self.stack
