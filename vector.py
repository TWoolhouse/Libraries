from math import radians, sin, cos, sqrt

class Vector(object):
    """Simple N Component Vector"""

    def __init__(self, *values):
        if len(values) == 0:
            self.values = (0,)
        else:
            self.values = values

    def __repr__(self) -> str:
        return "{}".format(self.values)

    def __iter__(self): #can be iterated over
        return self.values.__iter__()

    def __len__(self): #allows len
        return len(self.values)

    def __hash__(self):
        return self.values.__hash__()

    def __abs__(self) -> "Vector":
        return self.__class__(*(abs(i) for i in self))

    def __neg__(self) -> "Vector":
        return self.__class__(*(-i for i in self))

    def int(self) -> "Vector":
        return self.__class__(*(int(i) for i in self))

    def float(self) -> "Vector":
        return self.__class__(*(float(i) for i in self))

    def round(self, ndigits=None) -> "Vector":
        return self.__class__(*(round(i, ndigits) for i in self))

    def __getitem__(self, key): #allows indexing
        return self.values[key]

    def __eq__(self, other: "Vector") -> bool:
        if isinstance(other, self.__class__):
            return all((a == b for a,b in zip(self, other)))

    def __ne__(self, other: "Vector") -> bool:
        if isinstance(other, self.__class__):
            return not all((a == b for a,b in zip(self, other)))

    def __add__(self, other: "Vector") -> "Vector": #can add
        if isinstance(other, self.__class__): #only allows other Vectors
            return self.__class__(*(a + b for a, b in zip(self, other)))
        else:   raise TypeError(self._opp_err("+", other))

    def __sub__(self, other: "Vector") -> "Vector": #can subtract
        if isinstance(other, self.__class__): #only allows other Vectors
            return self.__class__(*(a - b for a, b in zip(self, other)))
        else:   raise TypeError(self._opp_err("-", other))

    def __mul__(self, other: (float, "Vector")) -> ("Vector", int): #can multiply
        if isinstance(other, (int, float)): #scalar multiplication
            return self.__class__(*(a * other for a in self))
        elif isinstance(other, self.__class__): #two Vectors
            return self._dot_mul(other)
        elif isinstance(other, list) or (type(other).__name__ == "Matrix"):
            return self._matrix_mul(other)
        else:   raise TypeError(self._opp_err("*", other))

    def __rmul__(self, other: "Vector") -> ("Vector", int): #multiplication on the righthandside
        return self.__mul__(other)

    def __truediv__(self, other: float) -> "Vector": #division with /
        if isinstance(other, (int, float)): #only with a scalar
            return self.__class__(*(a / other for a in self))
        else:   raise TypeError(self._opp_err("/", other))

    def __floordiv__(self, other: float) -> "Vector": #division with //
        if isinstance(other, (int, float)): #only with a scalar
            return self.__class__(*(a // other for a in self))
        else:   raise TypeError(self._opp_err("//", other))

    def __mod__(self, other: float) -> "Vector":
        if isinstance(other, (int, float)): #only with a scalar
            return self.__class__(*(a % other for a in self))
        else:   raise TypeError(self._opp_err("%", other))

    def _matrix_mul(self, other: "Vector") -> "Vector": #matrix multiplication
        if all(len(row) == len(self) for row in other) and (len(other) == len(self)): #has to have the same dimensions
            _temp = [self.__class__(*row)*scale for scale, row in zip(self, other)]
            return self.__class__(*(sum([o[i] for o in _temp]) for i in range(len(_temp))))
        else:   raise ValueError("Matrix must have the same dimensions as the Vector")

    def _dot_mul(self, other: "Vector") -> float: #dot multiplication
        return sum(a * b for a, b in zip(self, other))

    def _rotate2D(self, theta: float) -> "Vector":
        theta = radians(theta)
        return self._matrix_mul([[cos(theta), sin(theta)],[-sin(theta), cos(theta)]])

    def rotate(self, other: (float, "Vector")) -> "Vector":
        """Takes an angle in degrees and rotates in 2D. It can also take a matrix and use that as a rotation matrix"""
        if isinstance(other, (int, float)):
            return self._rotate2D(other)
        else:
            return self._matrix_mul(other)

    def norm(self) -> "Vector":
        """Returns the normalized Vector"""
        self.values = tuple(self/self.mag())
        return self

    def sqr_mag(self) -> float:
        """Returns the square of the magnitude of the Vector"""
        return sum(a**2 for a in self)

    def mag(self) -> float:
        """Returns the magnitude of the Vector"""
        return sqrt(self.sqr_mag())

    def dist(self, other: "Vector", sqr=False) -> float: #distance between 2 vectors
        """Returns the distance between itself and another Vector"""
        if sqr:
            return (self-other).sqr_mag()
        return (self-other).mag()

    def limit(self, lim: float):
        """Limits the Vector to not exceed a certain magnitude"""
        if self.mag() > lim:
            self.values = tuple(self.norm()*lim)
        return self

    def map(self, other: "Vector") -> "Vector":
        """Multiplies each component with the corrosponding component of other"""
        return self.__class__(*(self[i] * other[i] for i in range(len(self))))

    def contrain(self, s1: "Vector", e1: "Vector", s2: "Vector", e2: "Vector") -> "Vector":
        """Resizes the Vector to be scaled within the args"""
        if all(map(lambda x: isinstance(x, self.__class__) and len(x) == len(self), (s1, e1, s2, e2))):
            return self.__class__(*( ((self[i] - s1[i]) / (e1[i] - s1[i])) * (e2[i] - s2[i]) + s2[i] for i in range(len(self)) ))
        raise TypeError("Args must be Vectors of same length as self")

    def within(self, *contraints: tuple, include: bool=False) -> bool:
        """Checks if all values in Vector are within a contraint that corresponds to its index"""
        if include:
            return all((contraint[0] <= value and value <= contraint[1] for value, contraint in zip(self, contraints)))
        return all((contraint[0] < value and value < contraint[1] for value, contraint in zip(self, contraints)))

    def clamp(self, lower: "Vector"=None, upper: "Vector"=None) -> "Vector":
        return self.__class__(*(
            (u if v > u else (l if v < l else v)) for v, l, u in zip(self, lower if lower else self, upper if upper else self)
        ))

    def _opp_err(self, opp, b):
        return "unsupported operand type(s) for {}: '{}' and '{}'".format(\
        opp, type(self).__name__, type(b).__name__)
