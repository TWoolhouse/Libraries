from interface import Interface
import asyncio
import queue
from collections import deque, defaultdict
from typing import Union, Awaitable, IO, overload
import enum
import io
import shutil
import sounddevice as sd
import soundfile as sf

class Status(enum.IntEnum):
    NONE = 0
    QUEUE = 1
    ACTIVE = 2
    DONE = 3
    SKIP = 4
    CLEAR = 5
    INVALID = 6

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

class __BaseTrack:

    def __init__(self, *args):
        self.path: str = None
        self.stream: IO = None
        self._fut: asyncio.Future = None
        self._ready = asyncio.Event()
        self._samplerate = 1
        self._duration = ChangeState(-1, "__ge__")
        self._status = ChangeState(Status.NONE, "__eq__")
        self._duration_total = 0

    def __await__(self):
        return self.wait().__await__()

    @property
    def status(self) -> Status:
        return self._status.value
    @property
    def duration(self) -> int:
        return self._duration.value

    async def wait(self, duration=None, type: str="%") -> Status:
        if self._status.value >= Status.DONE:
                return self._status.value
        elif isinstance(duration, Status): # Wait for Status
            return await self._status.add(duration)
        elif duration is not None: # Wait for duration
            if not duration:
                pass
            elif type == "%": # Percentage
                await self._ready.wait()
                duration = max(min(duration, 1), -1) * self._duration_total
            elif type == "s": # Seconds
                await self._ready.wait()
                duration *= self._samplerate
            # Frames
            if duration < 0:
                if not self._duration_total:
                    raise ValueError("Total Duration Unknown")
                await self._ready.wait()
                duration += self._duration_total
            return await self._duration.add(int(duration))
        elif self._fut is not None: # Wait til end
            return await self._fut
        return self._status.value

    async def _read(self, size: int) -> list:
        raise NotImplementedError
    def _open(self) -> bool:
        return True
    async def _preload(self, samplerate: int, channels: int, format: str):
        self._ready.set()
    async def _close(self):
        pass

    def copy(self):
        raise NotImplementedError

class TrackPath(__BaseTrack):
    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._file = None

    async def _read(self, size: int) -> list:
        return self._file.buffer_read(size, self._format)

    async def _preload(self, samplerate: int, channels: int, format: str):
        self._format = format
        self._file = sf.SoundFile(self.path)
        self._duration_total = int(self._file.frames)
        self._ready.set()
    async def _close(self):
        if self._file is not None:
            self._file.close()

    def copy(self):
        return self.__class__(self.path)

class TrackFile(__BaseTrack):
    def __init__(self, file: IO):
        super().__init__()
        raise NotImplementedError

class Track:

    def __new__(cls, arg, *args, **kwargs):
        if isinstance(arg, str):
            return TrackPath(arg, *args, **kwargs)
        if isinstance(arg, io.IOBase):
            return TrackFile(arg, *args, **kwargs)
        # if isinstance()
        return super().__new__(cls)

    @overload
    def __init__(self, path: str): ...
    # @overload
    # def __init__(self, stream: IO): ...

    def __init__(self, path: str):
        self.status: Status = Status
        self.duration: int = 0
        raise NotImplementedError
    def __await__(self):
        return self.wait().__await__()

    @overload
    def wait(self) -> Status:
        """Wait for the Track to Finish Playing"""
    @overload
    def wait(self, duration: int, type: str="%"):
        """Wait for Duration to Pass"""
    @overload
    def wait(self, status: Status):
        """Wait for the status to match"""

    async def wait(self) -> Status:
        raise NotImplementedError
    def copy(self) -> 'Track':
        raise NotImplementedError

class Player:

    Track = Track
    Status = Status
    __DTYPE = "float32"

    def __init__(self, blocksize: int=4096, buffersize: int=8, samplerate: int=None):
        self.__active = None
        self.__tracks = deque()
        self.__buffer = queue.Queue()
        self.__buffer_size = asyncio.Semaphore(buffersize)
        self.__event = asyncio.Event()
        self.__event.set()

        self.__stream = sd.RawOutputStream(samplerate=samplerate, blocksize=blocksize, dtype=self.__DTYPE, callback=self.__stream_data_callback, finished_callback=self.__finished_callback)
        self.__SIZE_BLOCK = self.__stream.blocksize
        self.__SIZE_DATA = self.__SIZE_BLOCK * self.__stream.samplesize * self.__stream.channels

    def __await__(self):
        return self.__event.wait().__await__()

    async def __buffer_feeder(self):
        Interface.schedule(self.__stream.start)
        while self.__active or self.__get_next_track():
            await self.__buffer_size.acquire()
            await self.__active._ready.wait()
            data = await self.__active._read(self.__SIZE_BLOCK)
            self.__active._duration.value += self.__SIZE_BLOCK
            if len(data) < self.__SIZE_DATA:
                self.__get_next_track()
            self.__buffer.put_nowait(data)
        self.pause()

    def __get_next_track(self, reason: Status=Status.DONE) -> bool:
        if self.__active is not None:
            Interface.schedule(self.__active._close())
            self.__active._fut.set_result(reason)

        if not self.__tracks:
            self.__active = None
            self.pause()
            return False

        self.__active = track = self.__tracks.popleft()
        if not track._open():
            return self.__get_next_track(Status.INVALID)

        # Activating The Track
        track._duration.set(0)
        Interface.schedule(self.__activate_track(track))
        self.__preload()

        return True

    async def __activate_track(self, track: Track):
        await track._ready.wait()
        if track._status.value > Status.ACTIVE:
            v = track._status.value
            track._status.set(Status.ACTIVE)
            track._status.set(v)
        else:
            track._status.set(Status.ACTIVE)

    def __stream_data_callback(self, outdata: list, frames: int, time_info, status: sd.CallbackFlags):
        if status:
            print("SoundPlayer Status:", status)
        try:
            data = self.__buffer.get_nowait()
        except queue.Empty as e:
            print("Buffer Empty")
            return

        if len(data) < self.__SIZE_DATA:
            outdata[:len(data)] = data
            outdata[len(data):] = b"\x00" * (self.__SIZE_DATA - len(data))
        else:
            outdata[:] = data

        self.__buffer.task_done()
        Interface.loop.call_soon_threadsafe(self.__buffer_size.release)

    def __finished_callback(self):
        Interface.loop.call_soon_threadsafe(self.__event.set)

    def __preload(self):
        if self.__tracks and not self.__tracks[0]._ready.is_set():
            Interface.schedule(self.__tracks[0]._preload(self.__stream.samplerate, self.__stream.channels, self.__DTYPE))

    def __insert(self, track: Track, play: bool) -> Awaitable:
        if track._status.value is not Status.NONE:
            raise ValueError(f"Already Used Track: {track}")
        fut = track._fut = Interface.loop.create_future()
        track._status.set(Status.QUEUE)
        track._samplerate = self.__stream.samplerate
        fut.add_done_callback(track._status.chain)
        self.__preload()
        if play:
            self.play()
        return fut

    @property
    def active(self) -> Track:
        return self.__active

    def play(self):
        if self.__event.is_set():
            self.__event.clear()
            Interface.schedule(self.__buffer_feeder())

    def pause(self):
        self.__stream.stop()
        self.__event.set()

    def append(self, track: Track, play=True) -> Track:
        self.__tracks.append(track)
        self.__insert(track, play)
        return track
    def next(self, track: Track, play=True) -> Track:
        self.__tracks.appendleft(track)
        self.__insert(track, play)
        return track
    def extend(self, *tracks: Track, play=True) -> Track:
        self.__tracks.extend(track)
        self.__insert(track, play)
        return track

    def skip(self):
        self.__get_next_track(Status.SKIP)

    def clear(self, active=False) -> tuple:
        self.__tracks.clear()
        for track in self.__tracks:
            track._fut.set_result(Status.CLEAR)
        if active:
            raise NotImplementedError

    def cancel(self, track: Track):
        if track is self.__active:
            return self.skip()
        if track in self.__tracks:
            self.__tracks.remove(track)
            track._fut.set_result(Status.CLEAR)
