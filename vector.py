from math import radians, sin, cos, sqrt

class Vector(object):
    """Simple N Component Vector"""

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

    def __hash__(self):
        return self.values.__hash__()

    def int(self):
        return self.__class__(*(int(i) for i in self))

    def float(self):
        return self.__class__(*(float(i) for i in self))

    def round(self, ndigits=None):
        return self.__class__(*(round(i, ndigits) for i in self))

    def __getitem__(self, key): #allows indexing
        return self.values[key]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all((a == b for a,b in zip(self, other)))

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not all((a == b for a,b in zip(self, other)))

    def __add__(self, other): #can add
        if isinstance(other, self.__class__): #only allows other Vectors
            return self.__class__(*(a + b for a, b in zip(self, other)))
        else:   raise TypeError(self.opp_err("+", other))

    def __sub__(self, other): #can subtract
        if isinstance(other, self.__class__): #only allows other Vectors
            return self.__class__(*(a - b for a, b in zip(self, other)))
        else:   raise TypeError(self.opp_err("-", other))

    def __mul__(self, other): #can multiply
        if isinstance(other, (int, float)): #scalar multiplication
            return self.__class__(*(a * other for a in self))
        elif isinstance(other, self.__class__): #two Vectors
            return self._dot_mul(other)
        elif isinstance(other, list) or (type(other).__name__ == "Matrix"):
            return self._matrix_mul(other)
        else:   raise TypeError(self.opp_err("*", other))

    def __rmul__(self, other): #multiplication on the righthandside
        return self.__mul__(other)

    def __truediv__(self, other): #division with /
        if isinstance(other, (int, float)): #only with a scalar
            return self.__class__(*(a / other for a in self))
        else:   raise TypeError(self.opp_err("/", other))

    def __floordiv__(self, other): #division with //
        if isinstance(other, (int, float)): #only with a scalar
            return self.__class__(*(a // other for a in self))
        else:   raise TypeError(self.opp_err("//", other))

    def __mod__(self, other):
        if isinstance(other, (int, float)): #only with a scalar
            return self.__class__(*(a % other for a in self))
        else:   raise TypeError(self.opp_err("%", other))

    def _matrix_mul(self, other): #matrix multiplication
        if all(len(row) == len(self) for row in other) and (len(other) == len(self)): #has to have the same dimensions
            _temp = [self.__class__(*row)*scale for scale, row in zip(self, other)]
            return self.__class__(*(sum([o[i] for o in _temp]) for i in range(len(_temp))))
        else:   raise ValueError("Matrix must have the same dimensions as the Vector")

    def _dot_mul(self, other): #dot multiplication
        return sum(a * b for a, b in zip(self, other))

    def _rotate2D(self, theta):
        theta = radians(theta)
        return self._matrix_mul([[cos(theta), sin(theta)],[-sin(theta), cos(theta)]])

    def rotate(self, other):
        """Takes an angle in degrees and rotates in 2D. It can also take a matrix and use that as a rotation matrix"""
        if isinstance(other, (int, float)):
            return self._rotate2D(other)
        else:
            return self._matrix_mul(other)

    def norm(self):
        """Returns the normalized Vector"""
        self.values = tuple(self/self.mag())
        return self

    def sqr_mag(self):
        """Returns the square of the magnitude of the Vector"""
        return sum(a**2 for a in self)

    def mag(self):
        """Returns the magnitude of the Vector"""
        return sqrt(self.sqr_mag())

    def dist(self, other, sqr=False): #distance between 2 vectors
        """Returns the distance between itself and another Vector"""
        if sqr:
            return (self-other).sqr_mag()
        return (self-other).mag()

    def limit(self, lim):
        """Limits the Vector to not exceed a certain magnitude"""
        if self.mag() > lim:
            self.values = tuple(self.norm()*lim)
        return self

    def map(self, other):
        """Multiplies each component with the corrosponding component of other"""
        return self.__class__(*(self[i] * other[i] for i in range(len(self))))

    def contrain(self, s1, e1, s2, e2):
        """Resizes the Vector to be scaled within the args"""
        if all(map(lambda x: isinstance(x, self.__class__) and len(x) == len(self), (s1, e1, s2, e2))):
            return self.__class__(*( ((self[i] - s1[i]) / (e1[i] - s1[i])) * (e2[i] - s2[i]) + s2[i] for i in range(len(self)) ))
        raise TypeError("Args must be Vectors of same length as self")

    def opp_err(self, opp, b):
        return "unsupported operand type(s) for {}: '{}' and '{}'".format(\
        opp, type(self).__name__, type(b).__name__)
