import sys as __sys
import time as __time
import asyncio as __async
import functools as __functools
__print = print

flag = False

def __null(*args, **kwargs):
    return
def null(func):
    """Null Decorator"""
    return func

call = time = catch = log = null
print = print

class cfg:
    def __init__(self):
        self.output = None

class time_read:
    def __init__(self, func):
        self._func = func
    def total(self) -> float:
        return self._func._debug_time
    def count(self) -> int:
        return self._func._debug_count
    def time(self) -> float:
        return self._func._debug_time / self._func._debug_count
    def reset(self):
        self._func._debug_time = 0.0
        self._func._debug_count = 0

cfg = cfg()

def enable():
    global flag
    flag = True

    def name(f):
        try:
            return f.__qualname__
        except AttributeError:
            return f.__class__.__qualname__

    # Debug Print
    def print_log(*args, **kwargs):
        __print(*args, **({"file": __sys.stderr if cfg.output is None else cfg.output} | kwargs))

    # Logging
    def log(func):
        """Output Result of Func"""
        if __async.iscoroutinefunction(func):
            @__functools.wraps(func)
            async def debug_log(*args, **kwargs):
                res = await func(*args, **kwargs)
                print(name(func), args, kwargs, res)
                return res
            return debug_log
        else:
            @__functools.wraps(func)
            def debug_log(*args, **kwargs):
                res = func(*args, **kwargs)
                print(name(func), args, kwargs, res)
                return res
            return debug_log

    # Timmer
    def time(func):
        """Output Time Taken to Perfrom Func"""
        @__functools.wraps(func)
        def debug_time(*args, **kwargs):
            start = __time.time()
            res = func(*args, **kwargs)
            end = __time.time()
            debug_time._debug_time += end - start
            debug_time._debug_count += 1
            return res
        debug_time._debug_time = 0.0
        debug_time._debug_count = 0
        return debug_time

    # Catch Error and Output Input
    def catch(func):
        """Output Args & Kwargs if Func Throws"""
        if __async.iscoroutinefunction(func):
            @__functools.wraps(func)
            async def debug_catch(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    print(name(func), args, kwargs, name(e), e)
                    raise
            return debug_catch
        else:
            @__functools.wraps(func)
            def debug_catch(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(name(func), args, kwargs, name(e), e)
                    raise
            return debug_catch

    # Output Call
    def call(func):
        """Output Func Call Arguments"""
        @__functools.wraps(func)
        def debug_call(*args, **kwargs):
            print(name(func), args, kwargs)
            return func(*args, **kwargs)
        return debug_call

    to_update = {
        "print": print_log,
        "log": log,
        "time": time,
        "catch": catch,
        "call": call,
    }
    globals().update(**to_update)

def disable():
    global flag
    flag = False

    to_update = {
        "print": __null,
        **{f: null for f in ("log", "time", "catch", "call")},
    }
    globals().update(**to_update)

disable()
