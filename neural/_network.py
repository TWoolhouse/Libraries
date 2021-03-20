from .layout import Layout
from .neuron import N as Neuron
from typing import Callable, T
import pickle

class Network:

    def __init__(self, layout: Layout):
        self.layout = layout
        self._generate()

    def feed(self, *values: float) -> tuple[float]:
        """Send data into the network and return the output values"""
        self.clear()
        for n,v in zip(self._inputs, values):
            n.set(v)
        return [n.value() for n in self._outputs]

    def result(self, output: tuple[float], *funcs: Callable[..., T]) -> T:
        """Call the function that is in the same index as the highest output"""
        return max(zip(output, funcs))()

    def clear(self):
        for n in self._neurons:
            n.clear()

    def copy(self) -> 'Network':
        return pickle.loads(pickle.dumps(self)) # TODO: This is slow

    def __getstate__(self) -> tuple[Layout, tuple[Neuron]]:
        return self.layout, self._neurons
    def __setstate__(self, data: tuple[Layout, tuple[Neuron]]):
        self.layout, self._neurons = data
        self._inputs = [self._neurons[i] for i in self.layout.inputs]
        self._outputs = [self._neurons[i] for i in self.layout.outputs]

        for neuron in self._neurons:
            for con in [n for n in neuron._connections if isinstance(n, int)]:
                neuron._connections[self._neurons[con]] = neuron._connections.pop(con)

    def _generate(self):
        self._neurons: tuple[Neuron] = [n[2](n[0]) for n in self.layout.neurons]
        self._inputs: tuple[Neuron] = [self._neurons[i] for i in self.layout.inputs]
        self._outputs: tuple[Neuron] = [self._neurons[i] for i in self.layout.outputs]

        for neuron, data in zip(self._neurons, self.layout.neurons):
            neuron._connections |= {self._neurons[i]: 1.0 for i in data[1]}
