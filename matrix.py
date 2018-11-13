class Matrix(object):

    def __init__(self, *cols):
        """Takes arrays as the columns"""
        self.cols = [i for i in cols]
        for col in range(len(cols)):
            if type(cols[col]) != Column:
                self.cols[col] = Column(*cols[col])
        if not all(len(col) == len(self.cols[0]) for col in self.cols):
            raise ValueError("All columns must be the same size")

    def __repr__(self):
        x = []
        for row in range(len(self[0])):
            x.append(Column(*[item[row] for item in self]))
        return "{}".format("\n".join([str(i) for i in x]))

    def __len__(self):
        return len(self.cols)

    def __iter__(self):
        return self.cols.__iter__()

    def __getitem__(self, index):
        return self.cols[index]

    def __add__(self, other):
        if type(other) == type(self):
            if (len(other[0]) == len(self[0])) and (len(other) == len(self)):
                return Matrix(*(self[i] + other[i] for i in range(len(self))))
            else:   raise TypeError("Matrix must have the same dimensions")
        else:   raise TypeError(self.opp_err("+", other))

    def __sub__(self, other):
        if type(other) == type(self):
            if (len(other[0]) == len(self[0])) and (len(other) == len(self)):
                return Matrix(*(self[i] - other[i] for i in range(len(self))))
            else:   raise TypeError("Matrix must have the same dimensions")
        else:   raise TypeError(self.opp_err("-", other))

    def __mul__(self, other):
        if type(other) in (int, float):
            return Matrix(*(a * other for a in self))
        elif type(other) == Matrix:
            if len(self) == len(other[0]):
                return self.matrix_mul(other)
            else:   raise ValueError("Matrix does not have correct dimensions")
        else:   raise TypeError(self.opp_err("*", other))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other): #division with /
        if type(other) in (int, float): #only with a scalar
            return Matrix(*(a / other for a in self))
        else:   raise TypeError(self.opp_err("/", other))

    def __floordiv__(self, other): #division with //
        if type(other) in (int, float): #only with a scalar
            return Matrix(*(a // other for a in self))
        else:   raise TypeError(self.opp_err("//", other))

    def matrix_mul(self, other):
        """Returns a new Matrix after multiplying"""
        n_matrix = []
        for row in range(len(self[0])):
                n_matrix.append([col * (Column(*[item[row] for item in self])) for col in other])
        return Matrix(*n_matrix)

    def opp_err(self, opp, b):
        return "unsupported operand type(s) for {}: '{}' and '{}'".format(\
        opp, type(self).__name__, type(b).__name__)

class Column(object):

    def __init__(self, *values):
        self.values = values

    def __repr__(self):
        return "{}".format(" ".join([str(i) for i in self.values]))

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, index):
        return self.values[index]

    def __add__(self, other):
        if type(other) == type(self):
            if len(other) == len(self):
                return Column(*(a + b for a, b in zip(self, other)))
            else:   raise TypeError("Matrix must have the same dimensions")
        else:   raise TypeError(self.opp_err("+", other))

    def __sub__(self, other):
        if type(other) == type(self):
            if len(other) == len(self):
                return Column(*(a - b for a, b in zip(self, other)))
            else:   raise TypeError("Matrix must have the same dimensions")
        else:   raise TypeError(self.opp_err("-", other))

    def __mul__(self, other):
        if type(other) in (int, float):
            return Column(*(a * other for a in self))
        elif type(other) == Column:
            return sum(a * b for a, b in zip(self, other))
        else:   raise TypeError(self.opp_err("*", other))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other): #division with /
        if type(other) in (int, float): #only with a scalar
            return Column(*(a / other for a in self))
        else:   raise TypeError(self.opp_err("/", other))

    def __floordiv__(self, other): #division with //
        if type(other) in (int, float): #only with a scalar
            return Column(*(a // other for a in self))
        else:   raise TypeError(self.opp_err("//", other))
