import enum
import typing
import asyncio
import functools
import numpy as np
from asyio import StateWatcher
from interface import Interface
from dataclasses import dataclass
from typing import Any, Union, Callable, TypeVar

@dataclass
class Properties:
    dtype: str
    fmt: str
    channels: int
    samplerate: int
    size: int
    blocks: int
    def __bool__(self) -> bool:
        return self is not DEFAULT_PROP
DEFAULT_PROP = Properties("float32", "f32le", 2, 44100, 1, 1)

class Status(enum.IntEnum):
    INIT = 0
    QUEUE = 1
    PREPARE = 2
    READY = 3
    ACTIVE = 4
    DONE = 5
    CLEAR = 6
    SKIP = 7
    INVALID = 8

class ProcChain:
    def __init__(self, begin: type, end: type):
        self.chain: list['Processor'] = []
        self._cmd_queue: tuple[Callable[[Union[bytes, np.ndarray], int], Union[bytes, np.ndarray]]]
        self.io = [begin, end]

    def open(self, properties: Properties):
        for proc in self.chain:
            proc.open(properties)

        same = lambda a,b: (a is b) or (issubclass(a, typing.ByteString) and issubclass(b, typing.ByteString))
        def b2a(data: bytes) -> np.ndarray:
            return np.reshape(np.frombuffer(data, dtype=properties.dtype), (-1, properties.channels))
        a2b = np.ndarray.tobytes
        def convert(f, c):
            @functools.wraps(f)
            async def process(data, size):
                return await f(c(data), size)
            return process
        def out(c):
            @functools.wraps(c)
            async def process(data, size):
                return c(data)
            return process

        processors: list[Processor] = self.chain
        current = self.io[0]
        procs = []
        for proc in processors:
            f = proc.process
            ret = f.__annotations__["return"]
            _in = f.__annotations__["data"]
            if not same(_in, current):
                f = convert(f, b2a if _in == np.ndarray else a2b)
            procs.append(f)
            current = ret
        if not same(current, self.io[1]):
            procs.append(out(a2b if current == np.ndarray else b2a))
        self._cmd_queue = tuple(procs)

    def close(self):
        for proc in self.chain:
            proc.close()

    async def execute(self, data: Union[np.ndarray, bytes], size: int) -> Union[np.ndarray, bytes]:
        for func in self._cmd_queue:
            data = await func(data, size)
        return data

class NodeMeta(type):
    def __init__(self, name, bases, attrs):
        def wrap(func):
            if asyncio.iscoroutinefunction(func):
                async def close(self):
                    if not self._Node__closed:
                        await func(self)
            else:
                def close(self):
                    if not self._Node__closed:
                        func(self)
            return close
        if "close" in attrs:
            self.close = wrap(self.close)
        return super().__init__(name, bases, attrs)

class Node(metaclass=NodeMeta):

    def __init__(self):
        super().__init__()
        self.prop = DEFAULT_PROP
        self.__closed = False

    async def process(self, size: int) -> np.ndarray:
        pass
    def open(self, properties: Properties) -> bool:
        """Open the node before reading / processing can occur"""
        if self.prop is properties:    return True
        if self.prop:
            raise RuntimeError("Rebinding!")
        self.prop = properties
        self.__closed = False
        Interface.terminate.schedule(self.close)
        return False
    def close(self):
        """Closes the node after all reading / processing has finished"""
        self.__closed = True
        self.prop = DEFAULT_PROP

class Processor(Node):
    async def process(self, data: np.ndarray, size: int) -> np.ndarray:
        return data

class Flow(Node):
    def __init__(self):
        super().__init__()
        self.proc = ProcChain(
            self.read.__annotations__["return"],
            self.process.__annotations__["return"],
        )
        self.status: StateWatcher[Status] = StateWatcher(Status.INIT, "__ge__")

    def __await__(self):
        return self.status.wait(Status.DONE).__await__()

    async def process(self, size: int) -> np.ndarray:
        """Retrieve a fixed size block of audio after processing"""
        return await self.proc.execute(await self.read(size), size)

    async def read(self, size: int) -> Union[np.ndarray, bytes]:
        """Calculate the fixed size block before processing"""
        pass

    async def open(self, properties: Properties):
        """Open the stream before reading / processing can occur"""
        super().open(properties)
        self.proc.open(properties)
        return Interface.chain(self.status.wait(Status.DONE), self.close)
    async def close(self):
        """Closes the stream after all reading / processing has finished"""
        super().close()
        self.proc.close()
        if self.status.value < Status.DONE:
            self.status.set(Status.CLEAR)

@dataclass
class TrackInfo:
    name: str = None
    # Track Name
    source: str = None
    # Data Source
    duration: int = None
    # Total Frames

class Track(Flow):

    def __init__(self):
        super().__init__()
        self.duration = StateWatcher(0, "__ge__")
        self.info = TrackInfo()

    async def process(self, size: int) -> np.ndarray:
        """Retrieve a fixed size block of audio after processing"""
        data = await super().process(size)
        self.duration.value += len(data)
        return data

    async def read(self, size: int) -> bytes:
        """Calculate the fixed size block before processing"""
        return b""

class Stream(Flow):
    pass

TS = TypeVar("TrackStream", Stream, Track, covariant=True)
