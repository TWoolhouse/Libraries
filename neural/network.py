from neural.layout import Layout

class Network:

    def __init__(self, layout: Layout):
        self.layout = layout
        self.__inputs, self.__outputs, self._neurons = self.layout.compile()

    def input(self, *values: float) -> [float,]:
        self.clear()
        for n, v in zip(self.__inputs, values):
            n.set(v)
        return self.output()

    def output(self) -> [float,]:
        return [output.value() for output in self.__outputs]

    def clear(self):
        for neuron in self._neurons:
            neuron.set(None)

    def __getstate__(self) -> tuple:
        return self.layout, self._neurons, tuple(i.id for i in self.__inputs), tuple(i.id for i in self.__outputs)
    def __setstate__(self, data: tuple):
        l, n, i, o = data
        self.layout, self._neurons, self.__inputs, self.__outputs = l, n, tuple(n[v] for v in i), tuple(n[v] for v in o)

    def copy(self) -> "Network":
        network = Network(self.layout)
        for original, new in zip(self._neurons, network._neurons):
            id, bias, connections = original.__getstate__()
            connections = {key: [network._neurons[key], connections[key][1]] for key in connections}
            new.__setstate__((id, bias, connections))
        return network