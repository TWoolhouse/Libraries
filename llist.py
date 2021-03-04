from typing import Any, Iterator, Optional, Sequence, T, Union
from collections import deque

class LinkedList(Sequence[T]):
    def __init__(self, value: T, next: Optional['LinkedList[T]']=None):
        self.value: T = value
        self.next: Union[LinkedList[T], None] = next

    def final(self) -> 'LinkedList[T]':
        return deque(self.__iter__(), 1).pop()

    def __getitem__(self, key: int) -> 'LinkedList[T]':
        try:
            it = iter(self)
            for _ in range(key):
                next(it)
            return next(it)
        except StopIteration:
            raise IndexError(f"{self.__class__.__qualname__} index '{key}' out of range") from None

    def __setitem__(self, key: int, value: 'LinkedList[T]') -> 'LinkedList[T]':
        try:
            it = iter(self)
            for _ in range(key-1):
                next(it)
            p = next(it)
            if c := next(it, False):
                value.next = c.next
            p.next = value
            return c
        except StopIteration:
            raise IndexError(f"{self.__class__.__qualname__} index '{key}' out of range") from None

    def __delitem__(self, key: int) -> 'LinkedList[T]':
        try:
            it = iter(self)
            for _ in range(key-1):
                next(it)
            p = next(it)
            if c := next(it, None):
                p.next = c.next
            else:
                p.next = None
            return c
        except StopIteration:
            raise IndexError(f"{self.__class__.__qualname__} index '{key}' out of range") from None

    def __bool__(self) -> True:
        return True

    def __len__(self) -> int:
        return sum(1 for _ in self)
        # Deal with circular lists
        t = 0
        for c in self:
            if c is self and t:
                break
            t += 1
        return t

    def __add__(self, other: 'LinkedList[T]') -> 'LinkedList[T]':
        if not isinstance(other, LinkedList):
            raise TypeError
        end = other.final()
        end.next = self.next
        self.next = other
        return end

    def __iadd__(self, other: 'LinkedList[T]') -> 'LinkedList[T]':
        if not isinstance(other, LinkedList):
            raise TypeError
        end = other.final()
        end.next = self.next
        self.next = other
        return self

    def __iter__(self) -> Iterator['LinkedList[T]']:
        c = self
        yield c
        while c.next:
            c = c.next
            yield c

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}<{self.value}: {'X' if self.next else 'O'}>"

    def index(self, item: 'LinkedList[T]') -> int:
        raise NotImplementedError
    def count(self, item: 'LinkedList[T]') -> int:
        raise NotImplementedError

class LinkedView(Sequence[T]):
    def __init__(self, head: LinkedList[T], end: Union[int, LinkedList[T], None]=None, step: int=1):
        self.head = head
        self.end = end
        self.step = step

    def __getitem__(self, key: int) -> LinkedList[T]:
        return self.head.__getitem__(key * self.step)
    def __len__(self, key: int) -> LinkedList[T]:
        raise NotImplementedError

    def __iter__(self) -> Iterator[LinkedList[T]]:
        c = self.head
        yield c
        i = 0
        if isinstance(self.end, int):
            while c.next and (i+1) < self.end:
                i += 1
                c = c.next
                if not (i % self.step):
                    yield c
        elif isinstance(self.end, LinkedList):
            while c.next and c.next != self.end:
                i += 1
                c = c.next
                if not (i % self.step):
                    yield c
        else:
            while c.next:
                i += 1
                c = c.next
                if not (i % self.step):
                    yield c

class LinkedContainer(Sequence[T]):
    def __init__(self, head: LinkedList[T]):
        self.head = head
        self.end = self.head.final()

    def __getitem__(self, key: int) -> LinkedList[T]:
        return self.head.__getitem__(key)
    def __setitem__(self, key: int, value: LinkedList[T]) -> LinkedList[T]:
        if c:= self.head.__setitem__(key, value) and c is self.end:
            self.end = value
    def __delitem__(self, key: int) -> LinkedList[T]:
        if self.head.__delitem__(key) is self.end:
            self.end = self.head.final()

    def __len__(self) -> int:
        return self.head.__len__()
    def __iter__(self) -> Iterator[LinkedList[T]]:
        return self.head.__iter__()

    def __add__(self, other: 'LinkedContainer[T]') -> 'LinkedContainer[T]':
        if not isinstance(other, LinkedContainer):
            raise TypeError
        self.end = self.end + other.head
        return self

    def append(self, item: LinkedList[T]):
        self.end += item

LinkedList.__qualname__ = "l"

SIZE = 10
e = f = LinkedList(0)
for i in range(1, SIZE+1):
    e.next = LinkedList(i)
    e = e.next

e = g = LinkedList(SIZE+1)
for i in range(SIZE+1, 2*SIZE+1):
    e.next = LinkedList(i)
    e = e.next

e = h = LinkedList(SIZE+1)
for i in range(2*SIZE+1, 3*SIZE+1):
    e.next = LinkedList(i)
    e = e.next

print("LinkedList F:", *f)
print("LinkedList G:", *g)
print("LinkedList H:", *h)
print()

# a = f + g + h

f.final() + g
v = LinkedView(f, -1, 2)
print(*f)
print(*v)
