import math

def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))

class Neuron:
    def __init__(self, id: int, bias: float=0, value:float =None):
        self.id = id
        self.connections = {}
        self.bias = bias
        self._value = value

    def __repr__(self) -> str:
        return "{}-{}".format(self.__class__.__name__, self.id)

    def __eq__(self, other) -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return self.__repr__().__hash__()

    @property
    def value(self):
        if self._value is None:
            self._value = sigmoid(sum((neuron.value * weight for neuron, weight in self.connections.items())) + self.bias)
        return self._value

    def clear(self, value=None):
        self._value = value
        return self

class Layout:
    def __init__(self, inputs: int, outputs: int, template: tuple):
        self.inputs = inputs
        self.outputs = outputs
        self.template = tuple(template)

    def new(self) -> tuple:
        neurons = [Neuron(i) for i in range(len(self.template))]
        for neuron, t in zip(neurons, self.template):
            for n in t:
                neuron.connections[neurons[n]] = 0
        return neurons[:self.inputs], neurons[self.inputs:-self.outputs], neurons[-self.outputs:], neurons

    __call__ = new

    @classmethod
    def FeedForward(cls, inputs: int, outputs: int, layers: (int,)) -> object:
        if isinstance(layers, int):
            layers = [inputs] * layers
        layers = [inputs, *layers, outputs]

        template = []
        for index, size in enumerate(layers[1:], start=1):
            for node in range(size):
                value = sum(layers[:index-1])
                template.append(tuple((value+i for i in range(layers[index-1]))))
        return cls(inputs, outputs, (*[tuple() for i in range(inputs)], *template))

class Network:

    template = None # Layout

    def __init_subclass__(cls, template: Layout = None):
        cls.template = template

    def __init__(self, *neurons: (float,((int, float),))):
        self.inputs, self.layers, self.outputs, self.neurons = self.template.new()
        self.mutable = (*self.layers, *self.outputs)
        for neuron, values in zip(self.mutable, neurons):
            if values[0] is not None:
                neuron.bias = values[0]
            for value in values[1]:
                if value is not None:
                    id, v = value
                    neuron.connections[self.neurons[id]] = v

    def input(self, *args) -> [float,]:
        for v,i in zip(args, self.inputs):
            i.clear(v)
        results = [output.value for output in self.outputs]
        self.clear()
        return results

    def clear(self):
        for neuron in self.layers:
            neuron.clear()
        for neuron in self.outputs:
            neuron.clear()

    @property
    def new(self) -> type:
        return self.__class__

class Algorithm:

    def __init_subclass__(cls, template: Network=False, **kwargs):
        if not template:
            sub_init_subclass = cls.__init_subclass__.__func__
            def _sub_init(sub_cls, **sub_kwargs):
                func = super(cls, sub_cls).__init_subclass__
                if func == sub_init_subclass:
                    func(**sub_kwargs)
                sub_init_subclass(sub_cls, **sub_kwargs)
            cls.__init_subclass__ = classmethod(_sub_init)
        else:
            if isinstance(template, Network):
                template = template.__class__
            cls.template = template

    def __init__(self, network=None):
        self.network = self.template() if network is None else network

    def input(self, *args, **kwargs):
        pass

def Neural() -> Algorithm:
    pass