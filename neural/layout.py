from .neuron import N as Neuron

class Layout:
    """A specification for the network.
    It tells the network how to link all the neurons togeather and what type they should be."""

    def __init__(self, input: tuple[int], output: tuple[int], neurons: tuple[tuple[int, tuple[int], type[Neuron]]]):
        self.inputs, self.outputs = input, output # Index of input and output neurons
        self.neurons = neurons # Array of neurons and links

    def __getstate__(self) -> tuple[tuple[int], tuple[int], tuple[tuple[int, tuple[int], type[Neuron]]]]:
        return self.inputs, self.outputs, self.neurons
    def __setstate__(self, data: tuple[tuple[int], tuple[int], tuple[tuple[int, tuple[int], type[Neuron]]]]):
        self.inputs, self.outputs, self.neurons = data

def FeedForward(inputs: tuple[int, type[Neuron]], outputs: tuple[int, type[Neuron]], *layers: tuple[int, type[Neuron]]) -> Layout:
    """Create the spec for a feed forward network.
    Where all nodes are directly connected to the next column of rows."""
    size = sum(i[0] for i in layers)
    grid = [inputs, *layers, outputs]
    inputs, outputs = tuple(range(inputs[0])), tuple(range(inputs[0]+size, inputs[0]+size+outputs[0]))

    layout = [[i, [], v[1]] for v in grid for i in range(v[0])]
    count = len(layout)
    for column in range(len(grid)-1, 0, -1):
        for row in range(grid[column][0]-1, -1, -1):
            count -= 1
            neuron = layout[count]
            neuron[0] = count
            sub = grid[column-1][0]
            start = count - sub - row
            for child in range(start, start+sub):
                neuron[1].append(child)
    return Layout(inputs, outputs, layout)
