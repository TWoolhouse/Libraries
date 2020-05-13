import neural.maths

class Neuron:

    def __init__(self, id: int, bias: float=0, value: float=None):
        self.id = id
        self.bias = bias
        self.__value = value
        self._connections = {}

    def value(self):
        if self.__value is None:
            self.__value = neural.maths.sigmoid(
                sum(neuron.value() * weight for neuron, weight in self._connections.values())
                + self.bias
            )
        return self.__value

    def set(self, value: float=None):
        self.__value = value

    def __hash__(self) -> int:
        return id(self)

    def __getstate__(self) -> tuple:
        return self.id, self.bias, self._connections
    def __setstate__(self, data: tuple):
        self.id, self.bias, self._connections = data
        self.__value = None