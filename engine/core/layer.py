import enum
from collections import defaultdict

__all__ = ["Type", "Data", "Mask", "Stack"]

class Type:
    """Layer Type is a collection of identifiers for Layer Type Items"""

    class Item:
        """The individual Items that are used as a label to group elements in the Layer Stack"""
        def __init__(self, name: str, value: int):
            """Should not be created by the user
            name: The name used to access through the type
            value: The weight used to sort the Stack
            """
            self.name = name
            self.value = value

        def __repr__(self) -> str:
            return f"{self.name}.{self.value}"

        def __lt__(self, other: "Item") -> bool:
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
        if key.startswith("_"):
            return super().__getattribute__(key)
        return self.__items[key.upper()]

    def __repr__(self) -> str:
        return f"{self._name}"

class Data:
    """Inserted into the Stack"""

    def __init__(self, type: Type.Item, func: callable, active: bool=True):
        """Data stores the function and Type.Item that will be inserted into the stack"""
        self.type = type
        self.func = func
        self.active = active

    def __call__(self, *args, **kwargs) -> object:
        """Calls the underlying function"""
        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        try:
            name = self.func.__qualname__
        except AttributeError:
            name = self.func
        return f"LayerData<{self.type}-{self.active} Func:{name}>"

class Mask:
    """Enables and Disables Type.Items when passed to the Stack"""

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
        self.layers = defaultdict(list)
        self.stack = []
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
        except ValueError:    print(self, layer) # REMOVE
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
