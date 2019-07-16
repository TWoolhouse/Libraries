from vector import Vector

class Dimension:

    def __init__(self, length, sub, val=None):
        self.length = length[0]
        if sub <= 0:
            self.storage = [val() for i in range(self.length)] if isinstance(val, type) else [val for i in range(self.length)]
        else:
            self.storage = [Dimension(length[1:], sub-1) for i in range(self.length)]

    def __repr__(self):
        return "{}".format(self.storage)

    def __iter__(self):
        return self.storage.__iter__()

    def __len__(self):
        return len(self.storage)

    def __getitem__(self, key):
        if type(key) in (int, slice):
            return self.storage[key]
        else:
            if len(key) == 1:
                return self.storage[key[0]]
            else:
                return self.storage[key[0]][key[1:]]

    def __setitem__(self, name, value):
        if type(name) in (int, slice):
            self.storage[name] = value
        else:
            if len(name) == 1:
                self.storage[name[0]] = value
            else:
                self.storage[name[0]][name[1:]] = value

    def index(self, x, start=0, end=-1):
        return self.storage.index(x, start, end)

    def _find(self, x):
        try:
            return self.storage.index(x)
        except ValueError:  pass
        if any([type(i) != Dimension for i in self.storage]):
            pass
        else:
            for child in range(len(self.storage)):
                y = self.storage[child]._find(x)
                if y != None:
                    return str(y)+" "+str(child)

    def all(self):
        _temp = []
        if any([type(i) != Dimension for i in self.storage]):
            for i in self.storage:
                _temp.append(i)
        else:
            for i in self.storage:
                _temp.extend(i.all())
        yield from _temp

class Grid(Dimension):
    """A fixed N-th Dimensional array"""

    def __init__(self, *size, val=None):
        """Size of each Dimension. init_val is set to None by default"""
        self.size = Vector(*size)
        self.storage = [Dimension(self.size[1:], len(self.size)-2, val=val) for i in range(self.size[0])]

    def __repr__(self):
        return "{} {}".format(self.size, self.storage)

    def find(self, x):
        """Returns the exact index of the item within the entire grid"""
        try:
            y = tuple(reversed([int(i) for i in self._find(x).split(" ")]))
        except AttributeError: raise ValueError("'{}' is not in Grid".format(x))
        return y

    def set(self, name, value):
        """Sets and item to a specific value"""
        self[self.find(name)] = value
