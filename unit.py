convert = {
    "Distance": {"m":1, "ls":299792458, "ly":9.4607304725808*10**15},
    "Time": {"s":1, "min":60, "hr":3600, "day":86400, "week":604800, "month":2592000, "year":31556952},
    "Mass": {"g":1},
    "Data": {"b":1, "B":8},
    "_Unit": {"":1}
    }

SI = {
    "f":10**-15, "p":10**-12, "n":10**-9, "µ":10**-6, "m":10**-3, "c":10**-2, "d":10**-1,
    "da":10**1, "h":10**2, "k":10**3, "M":10**6, "G":10**9, "T":10**12, "P":10**15
    }

#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#

class _Unit:

    def __init__(self, num=1, unit=""):
        self.num, self.unit = num, unit
        self.value = self.set_value()

    def __repr__(self):
        return "{} {}".format(self.num, self.unit)

    def conversion(self):
        _temp = convert[type(self).__name__]
        try:
            return _temp[self.unit]
        except KeyError:
            try:
                return {key: val for key, val in zip([k+v for v in _temp for k in SI], [SI[k]*_temp[v] for v in _temp for k in SI])}[self.unit]
            except KeyError:
                raise ValueError("'{}' is not a recognised unit".format(self.unit))

    def set_value(self):
        return self.num*self.conversion()

    def _convert(self, val):
        return val/self.conversion()

    def convert(self, val):
        return self.__class__(self._convert(val), self.unit)

    def val(self):
        return self.value

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return "{} {}".format(self.num, self.unit)

    def __add__(self, other):
        return self._operation("__add__", other)

    def __sub__(self, other):
        return self._operation("__sub__", other)

    def __mul__(self, other):
        return self._operation("__mul__", other)

    def __truediv__(self, other):
        return self._operation("__truediv__", other)

    def __floordiv__(self, other):
        return self._operation("__floordiv__", other)

    def __mod__(self, other):
        return self._operation("__mod__", other)

    def __pow__(self, other):
        return self._operation("__pow__", other)

    def __radd__(self, other):
        return self._operation("__radd__", other)

    def __rsub__(self, other):
        return self._operation("__rsub__", other)

    def __rmul__(self, other):
        return self._operation("__rmul__", other)

    def __rtruediv__(self, other):
        return self._operation("__rtruediv__", other)

    def __rfloordiv__(self, other):
        return self._operation("__rfloordiv__", other)

    def __rmod__(self, other):
        return self._operation("__rmod__", other)

    def __rpow__(self, other):
        return self._operation("__rpow__", other)

    def _operation(self, opp, other):
        if type(other) == type(self):
            return self.convert(getattr(self.value, opp)(other.value))
        elif type(other) in (int, float):
            return self.convert(getattr(self.value, opp)(other))
        else:
            raise TypeError(self.opp_err(opp.replace("_",""), other))

    def opp_err(self, opp, b):
        return "unsupported operand type(s) for {}: '{}' and '{}'".format(\
        opp, type(self).__name__, type(b).__name__)

class _CompoundUnit(_Unit):

    def __init__(self, num, aim, *units):
        if len(units) > len(aim):
            self.unit_err(*aim)
        try:
            units = [((globals()[a](0, unit) if unit != a else globals()[a]()) if type(unit) == str else (unit if type(unit).__name__ == a else self.unit_err(*aim))) for a, unit in zip(aim, units)]
        except ValueError:
            self.unit_err(*aim)
        units = [*units, *[globals()[a]() for a in aim[len(units):]]]
        self.num, self.units = num, units
        self.value = self.set_value()

    def __repr__(self):
        return "{} {}".format(self.num, "/".join([u.unit for u in self.units]))

    def __str__(self):
        return "{} {}".format(self.num, "/".join([u.unit for u in self.units]))

    def conversion(self):
        total = self.units[0].conversion()
        for item in self.units[1:]:
            total /= item.conversion()
        return total

    def unit_err(self, *units):
        raise TypeError("{} only accepts units: {}".format(\
        type(self).__name__, ", ".join(units)))

#------------------------------------------------------------------------------#

class Unit(_Unit):

    def __init__(self, num=0, unit="_Unit"):
        if unit == "_Unit":
            unit = [i for i in convert[type(self).__name__] if convert[type(self).__name__][i] == 1][0]
        super().__init__(num, unit)

    def add_unit(self, **units):
        for key in units:
            convert[type(self).__name__][str(key)] = units[key]

class CompoundUnit(_CompoundUnit):

    def __init__(self, num=0, *units):
        super().__init__(num, *units)

#------------------------------------------------------------------------------#

def create_unit(name, base_unit, **units):
    globals()[name] = type(name, (Unit,), {})
    convert[name] = {base_unit:1}
    for key in units:
        convert[name][str(key)] = units[key]

class Distance(Unit):
    def __init__(self, num=0, unit="m"):
        super().__init__(num, unit)
class Time(Unit):
    def __init__(self, num=0, unit="s"):
        super().__init__(num, unit)
class Mass(Unit):
    def __init__(self, num=0, unit="kg"):
        super().__init__(num, unit)
class Data(Unit):
    def __init__(self, num=0, unit="b"):
        super().__init__(num, unit)
class Speed(_CompoundUnit):
    def __init__(self, num=0, *units):
        super().__init__(num, ["Distance", "Time"], *units)
class Acceleration(_CompoundUnit):
    def __init__(self, num=0, *units):
        super().__init__(num, ["Distance", "Time", "Time"], *units)
class DataRate(_CompoundUnit):
    def __init__(self, num=0, *units):
        super().__init__(num, ["Data", "Time"], *units)
