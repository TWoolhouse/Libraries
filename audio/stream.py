import asyncio
import numpy as np
from collections import deque
from stream import StreamArray
from interface import Interface
from typing import Union, Callable, Any, Iterator
from .base import Properties, Stream, Flow, Status, TS, Track

def guard(stream: TS, parent: Stream, add: Callable[[TS], Any]=None, pop: Callable[[TS], Any]=None):
    if parent.prop and stream.prop != parent.prop:
        stream.status.set(Status.PREPARE)
        fut = Interface.schedulc(stream.open(parent.prop))
        fut.add_done_callback(lambda f: add(stream))
        fut.add_done_callback(lambda f: stream.status.set(Status.ACTIVE))
        def on_check(f):
            if not parent.prop:
                stream.close()
        fut.add_done_callback(on_check)
        if pop is not None:
            async def done():
                await fut
                pop(stream)
            Interface.chain(stream.status.wait(Status.DONE), done)
    else:
        add(stream)
        if pop is not None:
            stream.status.wait(Status.DONE).add_done_callback(lambda fut: pop(stream))

class Gate(Stream):
    def __init__(self, stream: TS, active: bool=True):
        super().__init__()
        self.stream = stream
        self.active = active

    def toggle(self):
        """Toggle if the gate is open or closed"""
        self.active = not self.active

    async def open(self, properties: Properties):
        """Open the Gate before reading / processing can occur"""
        await super().open(properties)
        self.stream.status.set(Status.PREPARE)
        await self.stream.open(properties)
        self.stream.status.set(Status.ACTIVE)

        self.stream.status.wait(Status.DONE).add_done_callback(lambda f: self.status.set(Status.DONE))
    async def close(self):
        """Closes the Gate after all reading / processing has finished"""
        await self.stream.close()
        await super().close()

    async def read(self, size: int) -> np.ndarray:
        """Read previous Track/Stream's processed data"""
        if self.active:
            return await self.stream.process(size)
        return np.zeros((size, self.prop.channels), self.prop.dtype)

NULL_TRACK = Track()
NULL_TRACK.info.duration = 1

class Queue(Stream):
    def __init__(self, size: int=1, finish: bool=False):
        """Queues track/streams to play after each other"""
        super().__init__()
        self.stream: TS = NULL_TRACK
        self.ready: deque[TS] = deque()
        self.queue: deque[TS] = deque()
        self.size: int = 1 if size < 1 else size
        self._finish = finish

    async def read(self, size: int) -> np.ndarray:
        return await self.stream.process(size)

    async def open(self, properties: Properties):
        await super().open(properties)
        await NULL_TRACK.open(self.prop)
        self._load()
        await self._collect(Status.INIT)

    # async def close(self):
    #     pass

    async def _collect(self, cause: Status):
        """Get next item from the queue"""
        self.stream.status.set(cause)

        if not self.ready:
            self.stream = NULL_TRACK
            if not self.queue and self._finish:
                self.status.set(Status.DONE)
            return False

        new: TS = self.ready.popleft()
        self._load()

        if (await new.status.wait(Status.READY)) is not Status.READY:
            return await self._collect(Status.INVALID)
        new.status.set(Status.ACTIVE)
        Interface.chain(new.status.wait(Status.DONE), self._collect(Status.DONE))
        self.stream = new

    def _load(self):
        if self.prop and len(self.ready) < self.size and self.queue:
            if (item := self.queue.popleft()).status.value is not Status.QUEUE:
                return self._load()
            item.status.set(Status.PREPARE)
            self.ready.append(item)
            Interface.schedulc(self._load_stream(item)).add_done_callback(lambda f: self._load())

    async def _load_stream(self, stream: TS):
        try:
            await stream.open(self.prop)
        except Exception as exc:
            stream.status.set(Status.INVALID)
            raise
        stream.status.set(Status.READY)

    def _add(self, stream: TS) -> TS:
        if stream.status.value is not Status.INIT:
            raise ValueError(f"Incorrect State '{stream.status.value}': {stream}")
        stream.status.set(Status.QUEUE)

    def append(self, stream: TS) -> TS:
        self._add(stream)
        self.queue.append(stream)
        self._load()

    def tracks(self) -> Iterator[TS]:
        yield self.stream
        yield from self.ready
        yield from self.queue

class Mixer(Stream):
    def __init__(self, finish: bool=False):
        """Combines muliple tracks to play over each other"""
        super().__init__()
        self.streams: list[TS] = []
        self._finish = finish

    async def read(self, size: int) -> np.ndarray:
        """Combine the previous Track/Stream's processed data"""
        isarr = await Interface.gather(*(s.process(size) for s in self.streams))
        total = np.zeros((max((0, *(len(arr) for arr in isarr))), self.prop.channels), self.prop.dtype)
        for arr in isarr:
            total[:len(arr)] += arr
        return total

    async def open(self, properties: Properties):
        """Open the mixer before reading / processing can occur"""
        await super().open(properties)
        for ts in self.streams:
            ts.status.set(Status.PREPARE)
            try:
                await ts.open(properties)
            except Exception as exc:
                ts.status.set(Status.INVALID)
                raise
            ts.status.set(Status.ACTIVE)

    async def close(self):
        """Closes the mixer after all reading / processing has finished"""
        for ts in self.streams:
            await ts.close()
        await super().close()

    def add(self, stream: TS, pop: bool=True) -> TS:
        """Add a stream to the mixer"""
        if stream in self.streams:
            return stream
        guard(stream, self, self.streams.append, self.pop)
        return stream

    def pop(self, stream: TS) -> TS:
        """Remove a stream from the mixer"""
        if stream in self.streams:
            self.streams.remove(stream)
        return stream

class Buffer(Stream):
    def __init__(self, stream: TS, size: int, blocks: int):
        super().__init__()
        self.stream = stream
        self.buffer: StreamArray
        self._counter = asyncio.Semaphore()
        self.size, self.blocks = size, blocks

    async def open(self, properties: Properties):
        """Open the Buffer before reading / processing can occur"""
        await super().open(properties)
        self.buffer = StreamArray(self.size, (self.size, self.prop.channels), self.prop.dtype)
        self.stream.status.set(Status.PREPARE)
        await self.stream.open(self.prop)
        self.stream.status.set(Status.READY)
        self.stream.status.wait(Status.DONE).add_done_callback(lambda f: self.status.set(Status.DONE))
        Interface.schedulc(self._execute())

    async def _execute(self):
        self.stream.status.set(Status.ACTIVE)
        while self.status.value < Status.DONE:
            await self._counter.acquire()
            self.buffer.write(await self.stream.process(self.size))

    async def close(self):
        """Closes the Gate after all reading / processing has finished"""
        await self.stream.close()
        self.buffer.close()
        await super().close()

    async def read(self, size: int) -> np.ndarray:
        """Read previous Track/Stream's processed data"""
        data = self.buffer.read(size)
        self._counter_control()
        return data

    def _read_raw(self, size: int) -> np.ndarray:
        return self.buffer.read(size)

    def _counter_control(self):
        self._counter._value = self.blocks - len(self.buffer)
        if self._counter._value > 0:
            self._counter._wake_up_next()
