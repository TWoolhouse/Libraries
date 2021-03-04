import enum
from collections import defaultdict
from typing import Callable, T as _T

__all__ = ["Type", "Data", "Mask", "Stack"]

class Type:
    """Layer Type is a collection of identifiers for Layer Type Items"""

    class Item:
        """The individual Items that are used as a label to group elements in the Layer Stack/Matrix"""
        def __init__(self, name: str, value: int):
            """Should not be created by the user
            name: The name used to access through the type
            value: The weight used to sort the Stack
            """
            self.name = name
            self.value = value

        def __hash__(self) -> int:
            return self.value

        def __repr__(self) -> str:
            return f"{self.name}.{self.value}"

        def __lt__(self, other: 'Item') -> bool:
            """Sorts based on the value"""
            return self.value < other.value

    def __init__(self, name: str, **objs: int):
        """Collection of Items that is effectivly a non-constant enum.
        objs is the key value pairs used to generate the items.
        Items are accessed as memeber variables of this object.
        """
        self._name = name
        self.__items = {"NONE": self.__class__.Item("NONE", 0), **{k.upper(): self.__class__.Item(k.upper(), v) for k,v in objs.items() if not k.startswith("_")}}
        self.__ord_items = sorted(self.__items.values())

    def get(self, key: str) -> Item:
        return self[key]
    def set(self, key: str, value: int) -> Item:
        self[key] = value
        return self[key]

    def __getitem__(self, key: str) -> Item:
        return self.__items[key.upper()]

    def __iter__(self):
        return self.__ord_items.__iter__()

    def __setitem__(self, key: str, value: int) -> Item:
        key = key.upper()
        if key in self.__items:
            item = self.__items[key]
            item.value = value
        else:
            item = self.__class__.Item(key, value)
            self.__items[key] = item
            self.__ord_items.append(item)
            self.__ord_items.sort()
        return item

    def __delitem__(self, key: str) -> Item:
        item = self.__items.pop(key.upper())
        try:
            item.value = None
            self.__ord_items.remove(item)
        except AttributeError:    pass
        self.__ord_items.sort()
        return item

    def __getattribute__(self, key: str) -> Item:
        try:
            return super().__getattribute__(key)
        except AttributeError:
            return self.__items[key.upper()]

    def __repr__(self) -> str:
        return f"LayerType<{self._name}>"

class Data:
    """Inserted into the Stack"""

    def __init__(self, type: Type.Item, func: Callable[..., _T], active: bool=True):
        """Data stores the function and Type.Item that will be inserted into the stack"""
        self.type = type
        self.func = func
        self.active = active

    def __call__(self, *args, **kwargs) -> _T:
        """Calls the underlying function"""
        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        try:
            name = self.func.__qualname__
        except AttributeError:
            name = self.func
        return f"LayerData<{self.type}-{self.active} Func:{name}>"

class Mask:
    """Enables and Disables Type.Items when passed to a Stack/Matrix"""

    def __init__(self, *types: Type.Item, invert: bool=False):
        """Will make only those in 'types' active.
        Will do the opposite when 'invert' is True.
        """
        self.types = types
        self.invert = invert

    def __repr__(self) -> str:
        return "LayerMask<{}>".format(", ".join(map(str, self.types)))

class Stack:
    """Stores ordered Data that executes in order of the Type.Item.value of each Data"""

    def __init__(self, type: Type, *layers: Data, mask: Mask=None):
        """type: All Data must be of the same Layer.Type
        mask: default mask to use when compiling
        """
        self.type = type
        self.layers: dict[Type, list[Data]] = defaultdict(list)
        self.stack: list[Data] = []
        self._mask = self.mask(mask)

        for layer in layers:
            self.layers[layer.type].append(layer)

    def mask(self, mask: Mask=None) -> Mask:
        """Update the Mask
        if 'mask' is None then enable all Type.Items"""
        if mask is None:
            self._mask = Mask(self.type.NONE, invert=True)
        else:
            self._mask = mask
        return self._mask

    def add(self, layer: Data) -> Data:
        """Add a Data to the Stack
        Does NOT compile the Stack again
        """
        self.layers[layer.type].append(layer)
        return layer
    def remove(self, layer: Data) -> Data:
        """Remove a Data to the Stack
        Does NOT compile the Stack again
        """
        try:
            self.layers[layer.type].remove(layer)
        except ValueError:    return layer
        return layer

    def compile(self, mask: Mask=True):
        """Compile the Stack
        if mask is anything but 'True', it will be passed into Stack.mask
        """
        self.stack.clear()
        if mask != True:
            self.mask(mask)
        for t in self.type:
            if (t in self._mask.types) != self._mask.invert:
                for layer in self.layers[t]:
                    if layer.active:
                        self.stack.append(layer)

    def activate(self, layer: Data, flag: bool=None) -> bool:
        """Toggle the active status of a specific layer
        Does NOT compile the Stack
        """
        if flag is None:
            layer.active = not layer.active
        else:
            layer.active = flag
        return layer.active

    def __call__(self, *args, **kwargs):
        """Passes arguments to all Data in the active Stack in order of the Stack"""
        for layer in self.stack:
            layer(*args, **kwargs)

    def __iter__(self) -> iter:
        return self.stack.__iter__()

    def __repr__(self) -> str:
        return "LayerStack<{}[{}] {}>".format(self.type.__name__, len(self.stack), ", ".join(f"{k.name}:{len(v)}" for k,v in self.layers.items()))

class Matrix:

    def __init__(self, type: Type, mask: Mask=None):
        self.type = type
        self.form: dict[Type.Item, set[Type.Item]] = defaultdict(set)
        self.matrix: dict[Type.Item, set[Type.Item]] = defaultdict(set)
        self._mask = self.mask(mask)

    def mask(self, mask: Mask=None) -> Mask:
        """Update the Mask
        if 'mask' is None then enable all Type.Items"""
        if mask is None:
            self._mask = Mask(self.type.NONE, invert=True)
        else:
            self._mask = mask
        return self._mask

    def make(self, row: Type.Item, *items: Type.Item):
        """Create Single Row of interaction"""
        self.form[row] = set(items)
    def add(self, row: Type.Item, item: Type.Item):
        """Add item to row layer"""
        self.form[row].add(item)
    def remove(self, row: Type.Item, item: Type.Item):
        """Remove item from row"""
        self.form[row].discard(item)
    def clear(self):
        """Empty the entire matrix"""
        self.form.clear()
    def empty(self, row: Type.Item):
        """Clear row"""
        del self.form[row]
    def update(self, rows: dict[Type.Item, set[Type.Item]]):
        """Set all rows"""
        self.form.update(rows)

    def compile(self, mask: Mask=True):
        """Compile the Matrix
        if mask is anything but 'True', it will be passed into Matrix.mask
        """
        self.matrix.clear()
        if mask != True:
            self.mask(mask)
        for row, items in tuple(self.form.items()):
            s = self.matrix[row]
            for i in items:
                if (i in self._mask.types) != self._mask.invert:
                    s.add(i)
                    self.matrix[i].add(row)

    def __iter__(self):
        return self.matrix.values().__iter__()

    def within(self, a: set[Type.Item], b: set[Type.Item]) -> bool:
        return any(not self.matrix[i].isdisjoint(a) for i in b)
