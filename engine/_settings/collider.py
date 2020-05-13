from collections import defaultdict

class Setting:
    def __init__(self):
        self.matrix = defaultdict(set, {
            0: {0,},

        })

    def update(self, matrix: dict):
        self.matrix.clear()
        self.matrix.update(matrix)
