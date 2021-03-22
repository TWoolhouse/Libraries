from ._network import Network
import random
from typing import Iterator

class Algorithm:
    def __init__(self, network: Network):
        self.network: Network = network

class Genetic(Algorithm):

    def __init__(self, network: Network, population: int, probability: float, weight: float=1.0):
        super().__init__(network)
        self.population_size: int = population
        self._active_population = {}
        self._probability, self._weight = probability, weight

    def population(self) -> Iterator[Network]:
        """Create / Retrieve the next generation population"""
        if self._active_population:
            return iter(self._active_population)
        self._active_population = {self.mutate(self.network.copy()): None for _ in range(self.population_size-1)}
        self._active_population[self.network] = None
        return iter(self._active_population)

    def fitness(self, network: Network, value):
        if network in self._active_population:
            self._active_population[network] = value
            return value
        raise KeyError("Network not in Algorithm")

    def mutate(self, network: Network) -> Network:
        """Takes network and mutates it by changing weights and biases of all the nodes."""
        for neuron in network._neurons:
            if random.random() <= self._probability:
                neuron.bias += (random.random() - 0.5) * self._weight
            for conn in neuron._connections:
                if random.random() <= self._probability:
                    neuron._connections[conn] += (random.random() - 0.5) * self._weight
        return network

    def merge(self, all=True):
        """Merge the networks togeather based on the highest fitness"""
        if all:
            def max_key(kv):
                if kv[1] is None:
                    raise ValueError("Not all networks have a fitness")
                return kv[1]
        else:
            max_key = lambda kv: kv[1]
        self.network: Network = max(self._active_population.items(), key=max_key)[0]
        self._active_population.clear()
        return self.network
