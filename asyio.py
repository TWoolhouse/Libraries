import asyncio
from interface import Interface
import subprocess
import urllib.request
import http.client
import collections
from typing import Union

__all__ = ["Counter", "MultiQueue", "Request", "Process", "ProcessFast", "StateWatcher"]

class MultiQueue:

    def __init__(self):
        self._loop = Interface.loop
        self.queues: dict[..., asyncio.Queue] = {}
        self._getters = collections.deque()

    def create(self, key, queue: asyncio.Queue):
        self.queues[key] = queue
    def delete(self, key):
        return self.queues.pop(key, None)
    def __getitem__(self, key) -> asyncio.Queue:
        return self.queues[key]

    async def get(self, *keys):
        """Await for a value from any of the queues from keys"""
        if not keys:
            raise KeyError("Need atleast 1 Key")
        queues = {self.queues[key] for key in keys}
        output = self._loop.create_future()

        tasks = {self._loop.create_task(self._get_one(output, q)) for q in queues}

        try:
            for queue in queues:
                try:
                    r = queue.get_nowait()
                    queue.task_done()
                    return r
                except asyncio.QueueEmpty:
                    pass

            return await output
        finally:
            for fut in tasks:
                fut.cancel()

    async def _get_one(self, output: asyncio.Future, queue: asyncio.Queue):
        while queue.empty(): # See asyncio.Queue implmentation
            fut = queue._loop.create_future()
            queue._getters.append(fut)
            try:
                await fut
            except:
                getter.cancel()
                try:
                    queue._getters.remove(getter)
                except ValueError:
                    pass
                if not queue.empty() and not getter.cancelled():
                    queue._wakeup_next(queue._getters)
                raise
        if not output.done():
            output.set_result(queue.get_nowait())
            queue.task_done()

    def qsize(self) -> int:
        return sum(q.qsize() for q in self.queues.values())

class Counter:
    def __init__(self, value: int=0):
        self.value = value
        self._fut = set()

    def __await__(self):
        return self.wait().__await__()
    async def wait(self):
        if not self.value: # Return instantly if counter is at 0
            return True

        fut = Interface.loop.create_future()
        self._fut.add(fut)
        return await fut

    def incr(self, value: int=1):
        self.value += abs(value)
        return self.value
    def decr(self, value: int=1):
        self.value -= min(self.value, abs(value))

        if not self.value:
            for fut in self._fut:
                fut.set_result(True)
            self._fut.clear()
        return self.value
    def clear(self):
        return self.decr(self.value)

class Process:

    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL

    def __init__(self, args, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=False, decode=True, **kwargs):
        self.args = args
        self.__started = asyncio.Event()
        # self.__proc
        self.__decode = decode

        async def start():
            nonlocal args
            if shell:
                if isinstance(args, str):
                    args = (args,)
                else:
                    args = (" ".join(map(str, args)),)
                subproc = Interface.loop.subprocess_shell
            else:
                subproc = Interface.loop.subprocess_exec
            factory = lambda: asyncio.subprocess.SubprocessStreamProtocol(asyncio.streams._DEFAULT_LIMIT, Interface.loop)
            transport, protocol = await subproc(factory, *args, stdin=stdin, stdout=stdout, stderr=stderr, **kwargs)
            self.__proc = asyncio.subprocess.Process(transport, protocol, Interface.loop)
            self.__started.set()

        Interface.schedule(start())

    def __await__(self):
        return self.read().__await__()

    @property
    def process(self) -> asyncio.subprocess.Process:
        if not self.__started.is_set():
            raise ValueError("Process has not started")
        return self.__proc

    async def communicate(self, input=None) -> (bytes, bytes):
        await self.__started.wait()
        return await self.__proc.communicate(input)

    async def read(self) -> subprocess.CompletedProcess:
        completed = subprocess.CompletedProcess(self.args, self.__proc.returncode, *await self.communicate())
        if self.__decode:
            completed.stdout = completed.stdout.decode()
            completed.stderr = completed.stderr.decode()
        return completed

class ProcessFast:

    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL

    def __init__(self, args, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=False, decode=True, **kwargs):
        if isinstance(args, subprocess.Popen):
            self.args = args.args
            self.__proc = args
        else:
            self.args = args
            self.__proc = subprocess.Popen(args, stdout=stdout, stderr=stderr, stdin=stdin, shell=shell, **kwargs)
        self.__decode = decode

    def __await__(self):
        return self.read().__await__()

    @property
    def process(self) -> subprocess.Popen:
        return self.__proc

    async def read(self) -> subprocess.CompletedProcess:
        while self.__proc.poll() is None:
            await Interface.next()
        completed = subprocess.CompletedProcess(self.__proc.args, self.__proc.returncode, self.__proc.stdout.read() if self.__proc.stdout else None, self.__proc.stderr.read() if self.__proc.stderr else None)
        if self.__decode:
            completed.stdout = completed.stdout.decode()
            completed.stderr = completed.stderr.decode()
        return completed

class Request:

    def __init__(self, url, **kwargs):
        self.__proc = Interface.process(urllib.request.urlopen, url, **kwargs)

    def __await__(self):
        return self.wait().__await__()

    async def wait(self) -> Union[http.client.HTTPResponse, urllib.request.URLopener]:
        return await self.__proc

class Nevent(asyncio.Event):
    def __init__(self, clear=True):
        super().__init__()
        self._value = clear
    def set(self):
        return super().clear()
    def clear(self):
        return super().set()
    def is_set(self):
        return not self._value

class StateWatcher:

    def __init__(self, value, func="__eq__"):
        self._val = value
        self._waiters = {}
        self._func = func

    @property
    def value(self):
        return self._val

    @value.setter
    def value(self, value):
        self._val = value
        func = getattr(self._val, self._func)
        for fut, val in tuple(self._waiters.items()):
            if func(val):
                fut.set_result(self._val)
                del self._waiters[fut]
        return value

    def wait(self, value) -> asyncio.Future:
        fut = Interface.loop.create_future()
        if getattr(self._val, self._func)(value):
            fut.set_result(self._val)
            return fut
        self._waiters[fut] = value
        return fut

    def chain(self, fut: asyncio.Future):
        self.value: Status = fut.result()

    def clear(self, cancel=False):
        for fut in tuple(self._waiters.keys()):
            if cancel:
                fut.set_exception(RuntimeError)
            else:
                fut.set_result(self._val)
            del self._waiters[fut]
