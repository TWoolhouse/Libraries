from _neural_network.base import Algorithm, Network, Neuron, Layout
# import dispatch
import random

class Reinforcement(Algorithm):
    pass

class Genetic(Reinforcement):

    def train(self, func: lambda Network: int, population: int, mutation: float, uncertainty: float):
        # Dispatch all of them
        fitness = [(self.network, func(self.network))]
        for network in (self.mutate(self.network, mutation, uncertainty) for i in range(population)):
            fitness.append((network, func(network)))
        # Pick 2 based on fitness score
        parents = random.choices(*zip(*fitness), k=2)
        # Update neural with new Network
        self.network = self.merge(*parents)

    @classmethod
    def mutate(cls, network: Network, mutation: float, uncertainty: float) -> Network:
        return cls.template(*(
                (neuron.bias + (random.random() - 0.5) * uncertainty if random.random() < mutation else 0,
                ((n.id, w + (random.random() - 0.5) * uncertainty if random.random() < mutation else 0)
                for n, w in tuple(neuron.connections.items())))
            for neuron in network.mutable))

    @classmethod
    def merge(cls, *networks: Network) -> Network:
        def pick(neuron, index):
            network = random.choice(networks)
            return network.mutable[index].connections[network.neurons[neuron.id]]
        r = ((random.choice(networks).mutable[index].bias, [(n.id, pick(n, index)) for n in neuron.connections]) for index, neuron in enumerate(networks[0].mutable))
        return cls.template(*r)

class Net(Network, template=Layout.FeedForward(5, 5, 3)):    pass

class Test(Genetic, template=Net):    pass

# print(Test.template)
t = Test()

bucket = [0 for i in range(5)]

def attempt(net: Network) -> int:
    values = [0, 20, 40, 60, 80]
    random.shuffle(values)
    fit = values[sorted([(i, v) for i, v in enumerate(net.input(*values))], key=lambda x: x[1], reverse=True)[0][0]]
    bucket[values.index(fit)] += 1
    return fit * 100

for i in range(10000):
    t.train(attempt, 500, 1.0, 0.2)
print(bucket)
values = [1, 2, 3, 4, 5]
x = [(values[i], v) for i, v in enumerate(t.network.input(*values))]
# x = t.network.input(1, 2, 3, 4, 5)
# y = t.network.input(5, 4, 3, 2, 1)
print(x)
