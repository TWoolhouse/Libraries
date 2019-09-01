#---Global Variables-----------------------------------------------------------#

convert = {
    "Unit": {"":1}
    }

SI = {
    "f":10**-15, "p":10**-12, "n":10**-9, "µ":10**-6, "m":10**-3, "c":10**-2, "d":10**-1,
    "da":10**1, "h":10**2, "k":10**3, "M":10**6, "G":10**9, "T":10**12, "P":10**15
    }

#---Classes--------------------------------------------------------------------#

class Unit:

    def __init__(self, num=0, unit="Unit"):
        self.num, self.unit = num, unit
        self.conversion = self.get_conversion(self.unit)
        self.value = self.num*self.conversion

    def __repr__(self):
        return "{} {}".format(self.num, self.unit)

    def get_conversion(self, unit):
        type_key = convert[type(self).__name__]
        if unit in type_key:
            return type_key[unit]
        si_t = ((si+t, SI[si]*type_key[t]) for t in type_key for si in SI)
        for i in si_t:
            if i[0] == unit:
                return i[1]
        raise ValueError("'{}' is not a recognised unit".format(unit))

    def convert(self, value):
        return self.__class__(value/self.conversion, self.unit)

    def __float__(self):
        return float(self.value)
    def __int__(self):
        return int(self.value)
    def __str__(self):
        return str(self.num)+" "+str(self.unit)

    def __getitem__(self, unit):
        return self.__class__(self.value/self.get_conversion(unit), unit)

    def __call__(self, unit):
        self.unit = unit
        self.conversion = self.get_conversion(self.unit)
        self.num = self.value / self.conversion
        return self

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

    def __eq__(self, other):
        return self._equality("__eq__", other)
    def __ne__(self, other):
        return self._equality("__ne__", other)
    def __lt__(self, other):
        return self._equality("__lt__", other)
    def __le__(self, other):
        return self._equality("__le__", other)
    def __gt__(self, other):
        return self._equality("__gt__", other)
    def __ge__(self, other):
        return self._equality("__ge__", other)

    def _equality(self, opp, other):
        if type(other) == type(self):
            return getattr(self.value, opp)(other.value)
        elif type(other) in (int, float):
            return getattr(self.value, opp)(other)
        else:
            raise TypeError(self.opp_err(opp.replace("__",""), other))

    def _operation(self, opp, other):
        if type(other) == type(self):
            return self.convert(getattr(self.value, opp)(other.value))
        elif type(other) in (int, float):
            return self.convert(getattr(self.value, opp)(other))
        else:
            raise TypeError(self.opp_err(opp.replace("__",""), other))

    def opp_err(self, opp, b):
        return "unsupported operand type(s) for {}: '{}' and '{}'".format(\
        opp, type(self).__name__, type(b).__name__)

class CompoundUnit(Unit):

    aim = tuple()

    def __init__(self, num=0, *units):
        if len(units) > len(self.aim):
            raise TypeError("{} only accepts units: {}".format(type(self).__name__, ", ".join(self.aim)))
        elif len(units) < len(self.aim):
            units = (*units, *(None for i in range(len(units), len(self.aim))))

        self.num = num
        self.units = tuple((globals()[self.aim[i]]() if units[i] == None else globals()[self.aim[i]](0, units[i]) for i in range(len(self.aim))))
        self.conversion = self.get_conversion()
        self.value = self.num*self.conversion

    def get_conversion(self):
        total = self.units[0].conversion
        for u in self.units[1:]:
            total /= u.conversion
        return total

    def convert(self, value):
        return self.__class__(value/self.conversion, *(i.unit for i in self.units))

    def __repr__(self):
        return "{} {}".format(self.num, "/".join((i.unit for i in self.units)))
    def __str__(self):
        return "{} {}".format(self.num, "/".join((i.unit for i in self.units)))

#---Functions------------------------------------------------------------------#

def new(name, base_unit, **units):
    name = name.title().strip().replace(" ", "")
    cls = type(name, (Unit,), {})
    def __init__(self, num=0, unit=base_unit):
        super(cls, self).__init__(num, unit)
    setattr(cls, "__init__", __init__)
    convert[name] = {base_unit:1}
    for key in units:
        convert[name][str(key)] = units[key]
    globals()[name] = cls
    return cls

def create(name, *units):
    name = name.title().strip().replace(" ", "")
    cls = type(name, (CompoundUnit,), {"aim":tuple((i.title().strip().replace(" ", "") for i in units))})
    globals()[name] = cls
    return cls

#---Setup----------------------------------------------------------------------#

new("Distance", "m", ls=299792458, ly=9.4607304725808*10**15)
new("Time", "s", min=60, h=3600, day=86400, week=604800, month=2592000, year=31556952)
new("Mass", "g")
new("Data", "b", B=8)

# x = _Unit(1, "Gb")
# x.convert_base()
