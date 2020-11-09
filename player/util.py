import asyncio
from interface import Interface

class ChangeState:

    def __init__(self, value, func="__eq__"):
        self.val = value
        self._waiters = {}
        self._func = func

    @property
    def value(self):
        return self.val
    @value.setter
    def value(self, v):
        self.set(v)
        return v

    def set(self, value):
        self.val = value
        func = getattr(self.val, self._func)
        for fut, val in tuple(self._waiters.items()):
            if func(val):
                fut.set_result(self.val)
                del self._waiters[fut]
        return value

    def add(self, value) -> asyncio.Future:
        fut = Interface.loop.create_future()
        if getattr(self.val, self._func)(value):
            fut.set_result(self.val)
            return fut
        self._waiters[fut] = value
        return fut

    def chain(self, fut: asyncio.Future):
        self.set(fut.result())

    def clear(self, cancel=False):
        for fut in tuple(self._waiters.keys()):
            if cancel:
                fut.set_exception(RuntimeError)
            else:
                fut.set_result(self.val)
            del self._waiters[fut]