import layer
from collections import defaultdict

class Setting:
    def __init__(self):
        self.layers = layer.Type("ColliderLayer", )
        self.matrix = layer.Matrix(self.layers)

    def update(self, matrix: dict):
        self.matrix.clear()
        self.matrix.update(matrix)
