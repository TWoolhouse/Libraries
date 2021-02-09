import time
import debug
import asyncio
import functools
from typing import Callable
from interface import Interface

__all__ = ["cache", "Manager", "Cache", "AsyncCache"]

def cache(permanence, timeout: int=0):
    """permanence: int=1 the objects permanence"""
    cargs = (timeout,)
    if not callable(permanence):
        level = permanence
    else:
        level = 1

    def __cache_wrapper(func):
        if asyncio.iscoroutinefunction(func):
            instance = AsyncCache(func, level, *cargs)
            @functools.wraps(func)
            async def cache(*args, override=False, **kwargs):
                return await instance(override, *args, **kwargs)
        else:
            instance = Cache(func, level, *cargs)
            @functools.wraps(func)
            def cache(*args, override=False, **kwargs):
                return instance(override, *args, **kwargs)

        instance._func_wrap = cache
        Manager._instances[cache] = instance

        return cache

    if callable(permanence):
        return __cache_wrapper(permanence)
    else:
        return __cache_wrapper

class Cache:
    """Wrapper: Cache a function Call"""
    def __init__(self, func, permanence: int, timeout: int):
        """Wrapper: Cache a function Call"""
        self.func = func
        self._func_wrap = func
        self.cache = {}
        self.permanence = permanence
        self.timeout = timeout

        Manager._instances[self.func] = self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{len(self.cache)}{self.func}>"

    def __del__(self):
        for key in (self.func, self._func_wrap):
            Manager._instances.pop(key, None)

    def __call__(self, cache_disable: bool, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        try:
            if cache_disable:
                raise KeyError
            value = self.cache[key]
            value[1] = time.time()
            return value[0]
        except KeyError:
            res = self.cache[key] = [self.func(*args, **kwargs), time.time()]
            return res[0]

    def clear(self, *args, all=True):
        """Clear this Cache or specific Calls"""
        if all:
            self.cache.clear()
        else:
            return self.cache.pop(args)

    def discard(self, threshold: int):
        current = time.time()
        for key in {key for key, value in self.cache.items() if current - value[1] > threshold}:
            del self.cache[key]

    def __hash__(self) -> int:
        return self.func.__hash__()

class AsyncCache(Cache):

    async def __call__(self, cache_disable: bool, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        try:
            if cache_disable:
                raise KeyError
            value = self.cache[key]
            if isinstance(value, asyncio.Event):
                await value.wait()
            value = self.cache[key]
            value[1] = time.time()
            return value[0]
        except KeyError:
            event = self.cache[key] = asyncio.Event()
            res = self.cache[key] = [await self.func(*args, **kwargs), time.time()]
            event.set()
            return res[0]

    def clear(self, *args, all=True):
        """Clear this Cache or specific Calls"""
        if all:
            events = {e for e in self.cache.values() if isinstance(e, asyncio.Event)}
            self.cache.clear()
            for e in events:
                e.clear()
        else:
            e = self.cache.pop(args)
            if isinstance(e, asyncio.Event):
                e.clear()
            return e

    def discard(self, threshold: int):
        current = time.time()
        for key in {key for key, value in self.cache.items() if not isinstance(value, asyncio.Event) and current - value[1] > threshold}:
            del self.cache[key]

class Manager:
    def __init__(self):
        self._instances = {}
        self.permanence = 1

        @Interface.Repeat
        async def timeout_loop():
            self.timeout(self.permanence)
        timeout_loop.delay = 10
        timeout_loop()
        self._timer = timeout_loop

    @property
    def timer(self) -> float:
        return self._timer.delay
    @timer.setter
    def timer(self, value: float):
        self._timer.delay = value

    def clear(self, permanence: int=1):
        for cache in self._instances.values():
            if cache.permanence >= permanence:
                cache.clear()

    def discard(self, threshold: int, permanence: int=1):
        for cache in self._instances.values():
            if cache.permanence >= permanence:
                cache.discard(threshold)

    def __getitem__(self, key: Callable) -> Cache:
        return self._instances[key]

    def timeout(self, permanence: int=1):
        for cache in self._instances.values():
            if cache.permanence >= permanence:
                cache.discard(cache.timeout)

Manager = Manager()
