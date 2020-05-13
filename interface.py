import asyncio
import concurrent.futures
import functools
from typing import IO as _IO, Coroutine as _Coroutine, Callable as _Callable
import traceback

class Interface:

    def __init__(self):
        self.__executor_io = concurrent.futures.ThreadPoolExecutor()
        self.__executor_cpu = concurrent.futures.ProcessPoolExecutor()
        self.__loop = asyncio.get_event_loop()
        self.__active = asyncio.Event()
        self.__active.set()

    def active(self):
        return not self.__active.is_set()

    def stop(self):
        self.__active.set()
        self.__loop.stop()

    def serve(self):
        try:
            self.__active.clear()
            with self.__executor_cpu, self.__executor_io:
                self.__loop.run_forever()
        finally:
            self.__active.set()
            self.__loop.run_until_complete(self.__loop.shutdown_asyncgens())
            self.__loop.stop()
            self.__loop.close()

    def schedule(self, coroutine: _Coroutine) -> asyncio.Future:
        return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coroutine, self.__loop))

    async def process(self, func: _Callable, *args, execute_type: str="io", **kwargs):
        exec_func = functools.partial(func, *args, **kwargs)
        if execute_type == "cpu":
            return await self.__loop.run_in_executor(self.__executor_cpu, exec_func)
        else:
            return await self.__loop.run_in_executor(self.__executor_io, exec_func)

    @property
    def loop(self):
        return self.__loop

    class submit:

        def __init__(self, func: _Callable):
            self.__func = func
            self.__event = False
            self.__done = asyncio.Event()
            self.__done.set()
            self.__start = None
            self.__finally = None

        def cancel(self):
            self.__event = False

        def __await__(self):
            return self.__done.wait().__await__()

        def __call__(self, *args, **kwargs):
            return self.__run(*args, **kwargs)

        async def __run(self, *args, **kwargs):
            try:
                self.__event = True
                result = False
                if self.__start is not None:
                    await self.__start(*args, **kwargs)
                while self.__event and not result and Interface.active():
                    result = await self.__func(*args, **kwargs)
                    await asyncio.sleep(0)
            except Exception as e:
                print(f"Sumbit Error: {self.__func}", "".join(traceback.format_exception(e, e, e.__traceback__)))
            finally:
                if self.__finally is not None:
                    await self.__finally(*args, **kwargs)
                self.__event = False
                self.__done.set()

        def start(self, func):
            self.__start = func
            return func

        def final(self, func):
            self.__finally = func
            return func

    class __AioFile(_IO):

        def __init__(self, *args, **kwargs):
            self.__args, self.__kwargs = args, kwargs
            self.__file = None

        async def __aenter__(self):
            self.__file = await Interface.process(open, *self.__args, **self.__kwargs)
            return self.__file

        def __aexit__(self, *args):
            return Interface.loop.create_task(Interface.process(self.__file.close))

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

    def open(self, file: str, mode: str="r", *args, **kwargs) -> _IO:
        return self.__AioFile(file, mode, *args, **kwargs)

    def create(self) -> "Interface":
        return self.__class__()

    async def wait(self):
        await self.__active.wait()

Interface = Interface()
interface = Interface
