import enum
import typing
import asyncio
import functools
import threading
import numpy as np
import sounddevice as sd
from asyio import StateWatcher, Nevent
from stream import StreamArray
from interface import Interface
from typing import Union, Callable, Type
from collections import deque, namedtuple

Properties = namedtuple("StreamProperties", ["dtype", "channels", "samplerate", "size"])
properties_default = Properties("float32", 2, 44100, 8)
TrackStatus = namedtuple("TrackStatus", ["status", "duration"])

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

class TrackInfo:
    name: str = ""
    source: str = ""
    duration: int = 0

class Track:

    properties = properties_default

    def __init__(self):
        self.processors: list[Processor] = []
        self._procs: tuple[Callable] = ()
        self._blocksize = Processor.BLOCKSIZE
        self.state = TrackStatus(StateWatcher(Status.INIT, "__ge__"), StateWatcher(0, "__ge__"))
        self.info = TrackInfo()

    async def read(self, size: int) -> bytes:
        """Pre-Processing and buffering"""
        return b""
    async def open(self):
        return Interface.chain(self.state.status.wait(Status.DONE), Interface.terminate.schedule(self.close()))
    async def close(self):
        pass

    async def process(self):
        data = await self.read(self._blocksize)
        for func in self._procs:
            data = await func(data, self._blocksize)
        self.state.duration.value += len(data)
        return data

    def _bind(self, properties: Properties):
        """Bind to a Stream"""
        self.properties = properties
        for proc in self.processors:
            proc._bind(self.properties)
        self._procs, self._blocksize = Processor._compile(self.processors, self.read.__annotations__["return"], self.properties, np.ndarray)
    def _unbind(self):
        """Unbind from a stream"""
        self.properties = Track.properties
        self._procs = ()
        for proc in self.processors:
            proc._unbind()

class Processor:

    BLOCKSIZE: int = 1024
    properties = properties_default

    async def process(self, data: Union[bytes, np.ndarray], size: int) -> Union[bytes, np.ndarray]:
        pass

    @classmethod
    def _compile(cls, order: list['Processor'], input: Union[Type[bytes], Type[np.ndarray]], properties: Properties, output=np.ndarray) -> tuple[tuple[Callable], int]:
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

        blocksize = Processor.BLOCKSIZE
        current = input
        processes = []
        for proc in order:
            blocksize = max(blocksize, proc.BLOCKSIZE)
            ret = proc.process.__annotations__["return"]
            if not same(proc.process.__annotations__["data"], current):
                proc.process = convert(proc.process, b2a if proc.process.__annotations__["data"] == np.ndarray else a2b)
            processes.append(proc.process)
            current = ret
        # Output
        if not same(current, output):
            processes.append(out(a2b if current == np.ndarray else b2a))
        return tuple(processes), blocksize

    def _bind(self, properties: Properties):
        self.properties = properties
    def _unbind(self):
        self.properties = Processor.properties

class Mixer:

    properties = properties_default

class Stream:

    _mutex = threading.Lock()
    properties = properties_default
    BLOCKSIZE = 4096
    BUFFERSIZE = 32

    def __init__(self):
        self._active = Nevent()
        self.done = asyncio.Event()
        self.done.set()
        self._opened = False
        self._semaphore = asyncio.Semaphore(self.BUFFERSIZE)
        self._outdata: StreamArray = StreamArray(self.BLOCKSIZE, shape=(-1, self.properties.channels), dtype=self.properties.dtype)

    def active(self, flag: bool=None):
        if flag is None:
            return self._active.is_set()
        elif flag == False:
            self._active.clear()
        elif self._opened and self.properties is not Stream.properties:
            self._active.set()
        return self._active.is_set()

    def __await__(self):
        return self.wait().__await__()

    async def wait(self):
        await Interface.wait(self._active.wait(), self.done.wait())
        if not self._active.is_set() and self.done.is_set(): # Must check they are both still set
            return True
        return await self.wait()

    def __read_cond(self, size: int):
        self._semaphore._value = self.BUFFERSIZE - len(self._outdata._data)
        if self._semaphore._value:
            self._semaphore._wake_up_next()
            if not size and self._semaphore._value == self.BUFFERSIZE and self.done.is_set():
                self._active.clear()

    def read(self, size: int) -> np.ndarray:
        data = self._outdata.read(size)
        Interface.loop.call_soon_threadsafe(self.__read_cond, len(data))
        return data

    async def open(self):
        Interface.terminate.schedule(self.close())
        self._opened = True

    async def close(self):
        self._opened = False

    def _bind(self, properties: Properties):
        """Bind Tracks"""
        self.properties = properties
        self._outdata._shape = (-1, self.properties.channels)
        self._outdata._dtype = self.properties.dtype
    def _unbind(self):
        """Unbind Tracks"""
        self.properties = Stream.properties
        self._outdata._shape = (-1, self.properties.channels)
        self._outdata._dtype = self.properties.dtype

    async def _process_loop(self, fut):
        ready = await fut # Wait for opening
        self.active(ready or ready is None)
        while self._opened:
            await self._semaphore.acquire()
            data = await self.process()
            with self._mutex:
                self._outdata.write(data)
        self._active.clear()

    async def process(self):
        pass

class Controller:

    def __init__(self):
        self._stream = sd.OutputStream(dtype="float32", callback=self._stream_callback)
        self._inputs: set[Stream] = set()
        self._mutex = threading.Lock()
        self.properties = Properties(self._stream.dtype, int(self._stream.channels), int(self._stream.samplerate), int(self._stream.samplesize * self._stream.channels))
        Interface.terminate.schedule(self._stream.close)

    def _stream_callback(self, outdata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags):
        outdata.fill(0)
        count = 1
        with self._mutex:
            for stream in self._inputs:
                if stream._active.is_set():
                    count += 1
                    data = stream.read(frames)
                    outdata[:len(data)] += data

    def _bind(self, istream: Stream) -> Stream:
        """Bind a Stream with this Controller"""
        istream._mutex = self._mutex
        istream._bind(self.properties)
        return istream
    def _unbind(self, istream: Stream) -> Stream:
        istream._mutex = Stream._mutex
        istream._unbind()
        return istream

    def include(self, istream: Stream):
        """Include the istream to be played and _bind"""
        if istream.properties is not Stream.properties and istream.properties is not self.properties:
            raise ValueError("Rebinding!")
        self._bind(istream)
        Interface.schedulc(istream._process_loop(Interface.schedulc(istream.open())))
        self._inputs.add(istream)

    def discard(self, istream: Stream):
        """Discard the istream from being played and _unbind"""
        istream._active.clear()
        self._inputs.discard(istream)
        self._unbind(istream)
        Interface.schedulc(istream.close())
        return istream

    def play(self):
        """Begin audio processing"""
        if not self._stream.active:
            self._stream.start()
    def pause(self):
        """Stop audio processing"""
        self._stream.stop()
