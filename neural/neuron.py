from .maths import sigmoid as _sigmoid
from typing import TypeVar

class Neuron:

    def __init__(self, id: int, bias: float=0, value: float=None):
        self.id = id
        self.bias = bias
        self._value = value
        self._connections: dict[Neuron, float] = {}

    def value(self) -> float:
        if self._value is None:
            self._value = self._calc()
        return self._value

    def _calc(self) -> float:
        return (
            sum(neuron.value() * weight for neuron, weight in self._connections.items())
            + self.bias
        ) / max(1, len(self._connections))

    def _clear(self):
        self._value = None

    def __hash__(self) -> int:
        return id(self)

    def __getstate__(self) -> tuple[int, float, dict[int, float]]:
        return self.id, self.bias, {n.id: v for n,v in self._connections.items()}
    def __setstate__(self, data: tuple[int, float, dict[int, float]]):
        self.id, self.bias, self._connections = data
        self._value = None

N = TypeVar("N", bound=Neuron)
Hidden = Neuron

class Input(Neuron):
    def set(self, value: float):
        self._clear()
        self._value = value

class Output(Neuron):
    def _calc(self) -> float:
        return _sigmoid(super()._calc())

class Recurrent(Neuron):

    def __init__(self, id: int, bias: float=0, value: float=None):
        super().__init__(id, bias, value)
        self.previous: Neuron = Input(-id, bias, 0.0)
        self._connections[self.previous] = 1.0

    def _clear(self):
        self.previous.set(self._value)
        super()._clear()

    def __getstate__(self) -> tuple[int, float, dict[int, float], tuple[float, float]]:
        id, bias, cons = super().__getstate__()
        del cons[-self.id]
        return id, bias, cons, (self.previous.bias, self._connections[self.previous])

    def __setstate__(self, data: tuple[int, float, dict[int, float], tuple[float, float]]):
        super().__setstate__(data[:-1])
        self.previous = Input(-self.id, data[-1][0], 0.0)
        self._connections[self.previous] = data[-1][1]
