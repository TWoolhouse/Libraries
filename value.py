class Value(int):
    """Mutable Int"""

class Value(int):
    """Mutable Int"""

    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value)
    
    def __init__(self, *args, **kwargs):
        """Mutable Int
        
        Param: value, int
        """
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    def __add__(self, other: Value) -> Value:
        return self.__class__(super().__add__(other))
    def __divmod__(self, other: Value) -> Value:
        return self.__class__(super().__divmod__(other))
    def __floordiv__(self, other: Value) -> Value:
        return self.__class__(super().__floordiv__(other))
    def __mod__(self, other: Value) -> Value:
        return self.__class__(super().__mod__(other))
    def __mul__(self, other: Value) -> Value:
        return self.__class__(super().__mul__(other))
    def __pow__(self, other: Value) -> Value:
        return self.__class__(super().__pow__(other))
    def __sub__(self, other: Value) -> Value:
        return self.__class__(super().__sub__(other))
    def __truediv__(self, other: Value) -> Value:
        return self.__class__(super().__truediv__(other))

    def __bool__(self) -> bool:
        return super().__bool__()
    def __float__(self) -> float:
        return super().__float__()
    def __int__(self) -> int:
        return super().__int__()
    def __str__(self) -> str:
        return super().__str__()
    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: Value) -> bool:
        return super().__eq__(other)
    def __ge__(self, other: Value) -> bool:
        return super().__ge__(other)
    def __gt__(self, other: Value) -> bool:
        return super().__gt__(other)
    def __le__(self, other: Value) -> bool:
        return super().__le__(other)
    def __lt__(self, other: Value) -> bool:
        return super().__lt__(other)
    def __ne__(self, other: Value) -> bool:
        return super().__ne__(other)

    def __abs__(self) -> Value:
        return self.__class__(super().__abs__())
    def __index__(self) -> int:
        return super().__index__()
    def __invert__(self) -> Value:
        return self.__class__(super().__invert__())
    def __neg__(self) -> Value:
        return self.__class__(super().__neg__())
    def __pos__(self) -> Value:
        return self.__class__(super().__pos__())
    def __round__(self) -> Value:
        return self.__class__(super().__round__())

    def __and__(self, other: Value) -> Value:
        return self.__class__(super().__and__(other))
    def __lshift__(self, other: Value) -> Value:
        return self.__class__(super().__lshift__(other))
    def __rshift__(self, other: Value) -> Value:
        return self.__class__(super().__rshift__(other))
    def __or__(self, other: Value) -> Value:
        return self.__class__(super().__or__(other))
    def __xor__(self, other: Value) -> Value:
        return self.__class__(super().__xor__(other))

    def __radd__(self, other: Value) -> Value:
        return self.__class__(super().__radd__(other))
    def __rdivmod__(self, other: Value) -> Value:
        return self.__class__(super().__rdivmod__(other))
    def __rfloordiv__(self, other: Value) -> Value:
        return self.__class__(super().__rfloordiv__(other))
    def __rmod__(self, other: Value) -> Value:
        return self.__class__(super().__rmod__(other))
    def __rmul__(self, other: Value) -> Value:
        return self.__class__(super().__rmul__(other))
    def __rpow__(self, other: Value) -> Value:
        return self.__class__(super().__rpow__(other))
    def __rsub__(self, other: Value) -> Value:
        return self.__class__(super().__rsub__(other))
    def __rtruediv__(self, other: Value) -> Value:
        return self.__class__(super().__rtruediv__(other))

    def __rand__(self, other: Value) -> Value:
        return self.__class__(super().__rand__(other))
    def __rlshift__(self, other: Value) -> Value:
        return self.__class__(super().__rlshift__(other))
    def __rrshift__(self, other: Value) -> Value:
        return self.__class__(super().__rrshift__(other))
    def __ror__(self, other: Value) -> Value:
        return self.__class__(super().__ror__(other))
    def __rxor__(self, other: Value) -> Value:
        return self.__class__(super().__rxor__(other))
