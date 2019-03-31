from math import radians, sin, cos, sqrt

class Vector(object):

    def __init__(self, *values):
        if len(values) == 0:
            self.values = (0,)
        else:
            self.values = values

    def __repr__(self):
        return "{}".format(self.values)

    def __iter__(self): #can be iterated over
        return self.values.__iter__()

    def __len__(self): #allows len
        return len(self.values)

    def __getitem__(self, key): #allows indexing
        return self.values[key]

    def __add__(self, other): #can add
        if type(other) == type(self): #only allows other Vectors
            return Vector(*(a + b for a, b in zip(self, other)))
        else:   raise TypeError(self.opp_err("+", other))

    def __sub__(self, other): #can subtract
        if type(other) == type(self): #only allows other Vectors
            return Vector(*(a - b for a, b in zip(self, other)))
        else:   raise TypeError(self.opp_err("-", other))

    def __mul__(self, other): #can multiply
        if type(other) in (int, float): #scalar multiplication
            return Vector(*(a * other for a in self))
        elif type(other) == type(self): #two Vectors
            return self._dot_mul(other)
        elif (type(other) == list) or (type(other).__name__ == "Matrix"):
            return self._matrix_mul(other)
        else:   raise TypeError(self.opp_err("*", other))

    def __rmul__(self, other): #multiplication on the righthandside
        return self.__mul__(other)

    def __truediv__(self, other): #division with /
        if type(other) in (int, float): #only with a scalar
            return Vector(*(a / other for a in self))
        else:   raise TypeError(self.opp_err("/", other))

    def __floordiv__(self, other): #division with //
        if type(other) in (int, float): #only with a scalar
            return Vector(*(a // other for a in self))
        else:   raise TypeError(self.opp_err("//", other))

    def __mod__(self, other):
        if type(other) in (int, float): #only with a scalar
            return Vector(*(a % other for a in self))
        else:   raise TypeError(self.opp_err("%", other))

    def _matrix_mul(self, other): #matrix multiplication
        if all(len(row) == len(self) for row in other) and (len(other) == len(self)): #has to have the same dimensions
            _temp = [Vector(*row)*scale for scale, row in zip(self, other)]
            return Vector(*(sum([o[i] for o in _temp]) for i in range(len(_temp))))
        else:   raise ValueError("Matrix must have the same dimensions as the Vector")

    def _dot_mul(self, other): #dot multiplication
        return sum(a * b for a, b in zip(self, other))

    def _rotate2D(self, theta):
        theta = radians(theta)
        return self._matrix_mul([[cos(theta), sin(theta)],[-sin(theta), cos(theta)]])

    def rotate(self, other):
        """Takes an angle in degrees and rotates in 2D. It can also take a matrix and use that as a rotation matrix"""
        if type(other) in (int, float):
            return self._rotate2D(other)
        else:
            return self._matrix_mul(other)

    def norm(self):
        """Returns the normalized Vector"""
        self.values = tuple(self/self.mag())
        return self

    def mag(self):
        """Returns the magnitude of the Vector"""
        return sqrt(sum([a**2 for a in self]))

    def dist(self, other): #distance between 2 vectors
        """Returns the distance between itself and another Vector"""
        return (self-other).mag()

    def limit(self, lim):
        """Limits the Vector to not exceed a certain magnitude"""
        if self.mag() > lim:
            self.values = tuple(self.norm()*lim)
        return self

    def opp_err(self, opp, b):
        return "unsupported operand type(s) for {}: '{}' and '{}'".format(\
        opp, type(self).__name__, type(b).__name__)
