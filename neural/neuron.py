from .maths import sigmoid as _sigmoid

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
        return _sigmoid(
            sum(neuron.value() * weight for neuron, weight in self._connections.values())
            + self.bias
        )

    def _clear(self):
        self._value = None

    def __hash__(self) -> int:
        return id(self)

    def __getstate__(self) -> tuple:
        return self.id, self.bias, self._connections
    def __setstate__(self, data: tuple):
        self.id, self.bias, self._connections = data
        self._value = None

Hidden = Neuron

class Input(Neuron):
    def set(self, value: float):
        self._clear()
        self._value = value

class Recurrent(Neuron):

    def __init__(self, id: int, bias: float=0, value: float=None):
        super().__init__(id, bias, value)
        self.previous: Neuron = Input(-id, bias, 0.0)
        self._connections[self.previous] = 1.0

    def _clear(self):
        self.previous.set(self._value)
        super()._clear()

    def _calc(self) -> float:
        return _sigmoid(
            sum(neuron.value() * weight for neuron, weight in self._connections.values())
            + self.bias
        )
