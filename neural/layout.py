from neural.neuron import Neuron as _Neuron

class Layout:

    def __init__(self, data: tuple, input: tuple, output: tuple):
        self.__input, self.__output = input, output
        self.__data = data

    def compile(self) -> ((_Neuron,), (_Neuron,), [_Neuron,]):
        neurons = [_Neuron(i) for i in range(len(self.__data))]
        for neuron, connections in zip(neurons, self.__data):
            for conn in connections:
                neuron._connections[conn] = [neurons[conn], 0]
        return tuple(neurons[i] for i in self.__input), tuple(neurons[i] for i in self.__output), neurons

    def __getstate__(self) -> tuple:
        return self.__input, self.__output, self.__data
    def __setstate__(self, data: tuple):
        self.__input, self.__output, self.__data = data

def FeedForward(inputs: int, outputs: int, *layers: int) -> Layout:
    size = sum(layers)
    grid = [inputs, *layers, outputs]
    inputs, outputs = tuple(range(inputs)), tuple(range(inputs+size, inputs+size+outputs))

    layout = [[] for i in range(sum(grid))]
    count = len(layout)
    for column in range(len(grid)-1, 0, -1):
        for row in range(grid[column]-1, -1, -1):
            count -= 1
            neuron = layout[count]
            sub = grid[column-1]
            start = count - sub - row
            for child in range(sub):
                neuron.append(start + child)
    return Layout(layout, inputs, outputs)

