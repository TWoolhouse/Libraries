from neural.network import Network

import random

class Algorithm:
    def __init__(self, network: Network):
        self.network = network

class Genetic(Algorithm):
    def __init__(self, network: Network):
        super().__init__(network)
        self._pop = [[self.network, None]]
        self._iter = None

    def train(self, population: int, magnitude: float=1, probability: float=1) -> iter:
        self._pop = [[self.mutate(self.network.copy(), magnitude, probability), None] for i in range(population)]
        self._pop.insert(0, [self.network, None])
        self._iter = self.population()
        return self._iter

    def population(self) -> iter:
        for net in self._pop:
            fitness = yield net[0]
            if fitness is not None:
                net[1] = fitness
                yield
        self._iter = None

    def fitness(self, value):
        self._iter.send(value)

    def mutate(self, network: Network, magnitude: float=1, probability: float=1) -> Network:
        mag = magnitude * 2
        for neuron in network._neurons:
            if random.random() <= probability:
                neuron.bias += (random.random() - 0.5) * mag
            for conn in neuron._connections.values():
                if random.random() <= probability:
                    conn[1] += (random.random() - 0.5) * mag
        return network

    def merge(self):
        self.network = max((i for i in self._pop if i[1] is not None), key=lambda x: x[1])[0]
        self._pop = [self.network, None]
        return self.network

