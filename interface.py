import os
import queue
import asyncio
import functools
import threading
import traceback
import concurrent.futures
import multiprocessing as mp
from typing import Union, Any, IO, Coroutine, Callable, Awaitable

class Batch:
    def __init__(self):
        self.__trigger = False
        self.__callbacks = set()

    def schedule(self, function: Union[Coroutine, Callable, asyncio.Future], *args: Any, **kwargs: Any) -> asyncio.Future:
        fut = Interface.loop.create_future()
        async def execute():
            try:
                if not fut.cancelled():
                    return fut.set_result(await Interface.schedule(function, *args, **kwargs))
                if asyncio.iscoroutine(function):
                    function.throw(asyncio.CancelledError)
            except Exception as e:
                fut.set_exception(e)
        if self.__trigger:
            execute = execute()
        self.__callbacks.add(execute)
        return fut

    async def finish(self):
        self.__callbacks = {c() for c in self.__callbacks}
        self.__trigger = True
        while self.__callbacks:
            callbacks = self.__callbacks.copy()
            await Interface.wait(*callbacks)
            self.__callbacks -= callbacks
        self.__trigger = False

class Interface:

    def __init__(self):
        try:
            self.__loop = asyncio.get_event_loop()
        except RuntimeError:
            self.__loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__loop)
        self.__executor_io = concurrent.futures.ThreadPoolExecutor(thread_name_prefix=f"{self}-Thread")
        self.__executor_cpu = concurrent.futures.ProcessPoolExecutor()
        self.__loop.set_debug(False) # Debug
        self.__loop.set_default_executor(self.__executor_io)
        self.__active = asyncio.Event()
        self.__active.set()
        self.__thread = None

        self.terminate = Batch()

    def __repr__(self):
        if self.single():
            return f"{self.__class__.__name__}"
        return f"{self.__class__.__name__}<{mp.current_process().name}>"

    def active(self) -> bool:
        return not self.__active.is_set()

    def stop(self):
        if self.__thread != threading.current_thread():
            return self.schedule(self.stop)
        s = self.__active.is_set()
        self.__active.set()
        if not s:
            self.__loop.stop()

    def main(self):
        self.__thread = threading.current_thread()
        try:
            self.__active.clear()
            with self.__executor_cpu, self.__executor_io:
                self.__loop.run_forever()
        finally:
            self.__active.set()
            self.__loop.run_until_complete(self.terminate.finish())
            self.__loop.run_until_complete(self.next())
            self.__loop.run_until_complete(self.__loop.shutdown_asyncgens())
            self.__loop.stop()
            self.__loop.close()

    def schedulc(self, coro: Coroutine) -> asyncio.Future:
        """Schedule a coroutine fast"""
        return asyncio.ensure_future(coro, loop=self.__loop)

    def schedule(self, function: Union[Coroutine, Callable, asyncio.Future], *args: Any, **kwargs: Any) -> asyncio.Future:
        """Schedule the function/coroutine to be called"""
        if asyncio.iscoroutine(function): # Coroutine
            return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(function, self.__loop))
        elif asyncio.iscoroutinefunction(function): # Coroutine Function
            return self.schedule(function(*args, **kwargs))
        elif asyncio.isfuture(function): # Future
            return function
        elif callable(function): # Function
            fut = self.__loop.create_future()
            def execute():
                try:
                    if not fut.cancelled():
                        return fut.set_result(function(*args, **kwargs))
                except Exception as e:
                    fut.set_exception(e)
            self.__loop.call_soon_threadsafe(execute)
            return fut
        raise TypeError(f"'function' must be of type 'Coroutine', 'Callable', 'asyncio.Future' not '{function.__class__.__name__}'")

    def process(self, func: Union[Coroutine, Callable], *args, execute_type: str="io", **kwargs) -> asyncio.Future:
        exec_func = functools.partial(func, *args, **kwargs)
        if execute_type == "cpu":
            return self.__loop.run_in_executor(self.__executor_cpu, exec_func)
        else:
            return self.__loop.run_in_executor(self.__executor_io, exec_func)

    @property
    def loop(self):
        return self.__loop

    def create(self) -> "Interface":
        return self.__class__()

    def main_thread(self):
        def InterfaceThread():
            asyncio.set_event_loop(self.__loop)
            self.main()
        threading.Thread(target=InterfaceThread, name=self.__class__.__name__).start()

    def gather(self, *coro: Union[Coroutine, asyncio.Future], exception=False) -> asyncio.Future:
        return asyncio.gather(*coro, return_exceptions=exception)

    async def wait(self, *coro: Union[Coroutine, asyncio.Future]) -> list:
        return (await asyncio.wait(coro))[0]

    async def next(self, time: float=0):
        await asyncio.sleep(time)

    def chain(self, wait: asyncio.Future, func: Union[Coroutine, Callable, asyncio.Future], *args, **kwargs) -> asyncio.Future:
        fut = self.__loop.create_future()
        def chain_fut_func(f):
            asyncio.futures._chain_future(self.schedule(func, *args, **kwargs), fut)
        wait.add_done_callback(chain_fut_func)
        return fut

    def single(*_):
        return mp.current_process().name == "MainProcess"

    class Repeat:

        def __init__(self, func):
            self.__func = func
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def _func(*args, **kwargs):
                    return await func(*args, **kwargs)
            else:
                @functools.wraps(func)
                async def _func(*args, **kwargs):
                    return func(*args, **kwargs)
            self.__call__ = func # For autocomplete # Still broken
            setattr(self, "__call__", _func)

            self.__enter__ = self.__exit__ = None
            self.delay = 0

        def enter(self, func):
            self.__enter__ = func
            func.__name__ = f"{self.__func.__name__}.enter"
            return func
        def exit(self, func):
            self.__exit__ = func
            func.__name__ = f"{self.__func.__name__}.exit"
            return func

        class __instance:
            def __init__(self, parent, params):
                self.__parent = parent
                self.__params = params

                self.__done = asyncio.Event()
                self.__done.set()
                self.__event = True

                Interface.schedule(self.__main())

            def __await__(self):
                return self.__done.wait().__await__()
            async def wait(self):
                return await self.__done.wait()

            def cancel(self):
                self.__event = False

            async def __main(self):
                async with self:
                    try:
                        result = False
                        self.__done.clear()
                        while self.__event and not result and Interface.active():
                            await Interface.next(self.__parent.delay)
                            result = await self.__parent.__call__(*self.__params[0], **self.__params[1])
                    except Exception as e:
                        print(f"{self.__parent.__class__.__name__} Error: {self.__parent.__call__}", "".join(traceback.format_exception(e, e, e.__traceback__)))
                self.__event = False
                self.__done.set()

            async def __aenter__(self):
                if (func := self.__parent.__enter__) and asyncio.iscoroutine(f := func(*self.__params[0], **self.__params[1])):
                    await f
            async def __aexit__(self, *exit_args):
                if (func := self.__parent.__exit__) and asyncio.iscoroutine(f := func(*self.__params[0], **self.__params[1])):
                    await f

        def __call__(self, *args, **kwargs) -> __instance:
            instance = self.__instance(self, (args, kwargs))
            return instance

    class AIOFile(IO):

        def __init__(self, file: Union[str, bytes, int], *args, **kwargs):
            self.__file = None
            self.__args = (file, args, kwargs)

        def __await__(self):
            return self.__aenter__().__await__()

        async def __aenter__(self) -> IO:
            self.__file = await Interface.process(open, self.__args[0], *self.__args[1], **self.__args[2])
            return self.__file

        def __aexit__(self, *args):
            return Interface.process(self.__file.close)

        def __getattribute__(self, name: str):
            if name.startswith("_"):
                return super().__getattribute__(name)
            if self.__file is None:
                raise IOError("File not Open")
            return self.__file.__getattribute__(name)
        def __setattr__(self, name: str, value):
            if name.startswith("_"):
                return super().__setattr__(name, value)
            if self.__file is None:
                raise IOError("File not Open")
            return self.__file.__setattr__(name, value)

if Interface.single():
    Interface = Interface()
