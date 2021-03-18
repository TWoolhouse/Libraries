import math

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def constrain(n, start, stop):
    return (n - start) / (stop - start)
