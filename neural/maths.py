import math

def sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except:
        return 0

def constrain(n, start, stop):
    return (n - start) / (stop - start)
