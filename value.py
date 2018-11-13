class Value(float):

    def __new__(cls, value=0, *args, **kwargs):
        return super(Value, cls).__new__(cls, value)

    def __add__(self, other):
    	try:
    		return self.__class__(super().__add__(other))
    	except TypeError:
    		return NotImplemented
    def __sub__(self, other):
    	try:
    		return self.__class__(super().__sub__(other))
    	except TypeError:
    		return NotImplemented
    def __mul__(self, other):
    	try:
    		return self.__class__(super().__mul__(other))
    	except TypeError:
    		return NotImplemented
    def __truediv__(self, other):
    	try:
    		return self.__class__(super().__truediv__(other))
    	except TypeError:
    		return NotImplemented
    def __floordiv__(self, other):
    	try:
    		return self.__class__(super().__floordiv__(other))
    	except TypeError:
    		return NotImplemented
    def __mod__(self, other):
    	try:
    		return self.__class__(super().__mod__(other))
    	except TypeError:
    		return NotImplemented
    def __pow__(self, other):
    	try:
    		return self.__class__(super().__pow__(other))
    	except TypeError:
    		return NotImplemented
    def __radd__(self, other):
    	try:
    		return self.__class__(super().__radd__(other))
    	except TypeError:
    		return NotImplemented
    def __rsub__(self, other):
    	try:
    		return self.__class__(super().__rsub__(other))
    	except TypeError:
    		return NotImplemented
    def __rmul__(self, other):
    	try:
    		return self.__class__(super().__rmul__(other))
    	except TypeError:
    		return NotImplemented
    def __rtruediv__(self, other):
    	try:
    		return self.__class__(super().__rtruediv__(other))
    	except TypeError:
    		return NotImplemented
    def __rfloordiv__(self, other):
    	try:
    		return self.__class__(super().__rfloordiv__(other))
    	except TypeError:
    		return NotImplemented
    def __rmod__(self, other):
    	try:
    		return self.__class__(super().__rmod__(other))
    	except TypeError:
    		return NotImplemented
    def __rpow__(self, other):
    	try:
    		return self.__class__(super().__rpow__(other))
    	except TypeError:
    		return NotImplemented
