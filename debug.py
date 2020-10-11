import functools as __functools
import time as __time
import asyncio as __async
__print = print

flag = False

def __null(*args, **kwargs):
    return

def wrapper(func):
    return func
call = time = catch = log = wrapper
print = print

def enable():
    global flag
    flag = True

    def name(f):
        try:
            return f.__qualname__
        except AttributeError:
            return f.__class__.__qualname__

    # Logging
    def log(func):
        """Output Result of Func"""
        if __async.iscoroutinefunction(func):
            @__functools.wraps(func)
            async def debug_log(*args, **kwargs):
                res = await func(*args, **kwargs)
                __print(name(func), args, kwargs, res)
                return res
            return debug_log
        else:
            @__functools.wraps(func)
            def debug_log(*args, **kwargs):
                res = func(*args, **kwargs)
                __print(name(func), args, kwargs, res)
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
            __print(end - start)
            return res
        return debug_time

    # Catch Error and Output Input
    def catch(func):
        """Output Args & Kwargs if Func Throws"""
        if __async.iscoroutinefunction(func):
            @__functools.wraps(func)
            async def debug_catch(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    __print(name(func), args, kwargs)
                    raise
            return debug_catch
        else:
            @__functools.wraps(func)
            def debug_catch(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    __print(name(func), args, kwargs)
                    raise
            return debug_catch

    # Output Call
    def call(func):
        """Output Func Call Arguments"""
        @__functools.wraps(func)
        def debug_call(*args, **kwargs):
            __print(name(func), args, kwargs)
            return func(*args, **kwargs)
        return debug_call

    to_update = {
        "print": __print,
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
        **{f: wrapper for f in ("log", "time", "catch", "call")},
    }
    globals().update(**to_update)

disable()