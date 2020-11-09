import queue
import asyncio
import sounddevice as sd
from .Track import Track
from .Status import Status
from typing import Awaitable
from collections import deque
from interface import Interface
import traceback

class Player:

    Track = Track
    Status = Status
    __DTYPE = "float32"

    def __init__(self, blocksize: int=4096, buffersize: int=8, samplerate: int=None):
        self.__active = None
        self.__tracks = deque()
        self.__buffer = queue.Queue()
        self.__buffer_size = asyncio.Semaphore(buffersize)
        self.__buffer_feeder_active = False
        self.__event = asyncio.Event()
        self.__event.set()

        self.__stream = sd.RawOutputStream(samplerate=samplerate, blocksize=blocksize, dtype=self.__DTYPE, callback=self.__stream_data_callback, finished_callback=self.__finished_callback)
        self.__SIZE_BLOCK = self.__stream.blocksize
        self.__SIZE_DATA = self.__SIZE_BLOCK * self.__stream.samplesize * self.__stream.channels

    def __await__(self):
        return self.__event.wait().__await__()

    async def __buffer_feeder(self):
        Interface.schedule(self.__stream.start)
        if not self.__buffer_feeder_active:
            self.__buffer_feeder_active = True
            try:
                while self.__active or self.__get_next_track():
                    await self.__buffer_size.acquire()
                    try:
                        await self.__active._ready.wait()
                        data = await self.__active._read(self.__SIZE_BLOCK)
                    except Exception as e:
                        data = bytes()
                        traceback.print_exception(e, e, e.__traceback__)
                        # print(f"ERR {type(e).__name__}: {e}") # Weird Error
                    self.__active._duration.value += self.__SIZE_BLOCK
                    if len(data) < self.__SIZE_DATA:
                        self.__get_next_track()
                    self.__buffer.put_nowait(data)
            finally:
                self.__buffer.put_nowait(None)
                self.__buffer_feeder_active = False

    def __get_next_track(self, reason: Status=Status.DONE) -> bool:
        if self.__active is not None:
            Interface.schedule(self.__active._close())
            self.__active._fut.set_result(reason)

        if not self.__tracks:
            self.__active = None
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

        if data is None:
            raise sd.CallbackStop()

        if len(data) < self.__SIZE_DATA:
            outdata[:len(data)] = data
            outdata[len(data):] = b"\x00" * (self.__SIZE_DATA - len(data))
        else:
            outdata[:] = data

        self.__buffer.task_done()
        Interface.loop.call_soon_threadsafe(self.__buffer_size.release)

    def __finished_callback(self):
        self.pause()

    def __preload(self):
        if self.__tracks and not self.__tracks[0]._ready.is_set():
            Interface.schedule(self.__preload_wrap(self.__tracks[0]))
    async def __preload_wrap(self, track: Track):
        try:
            await track._preload(self.__stream)
        except Exception as e:
            async def _read_fail(*args):
                return bytes()
            track._read = _read_fail
            raise
        finally:
            track._ready.set()

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

    def reset(self):
        try:
            while True:
                self.__buffer.get_nowait()
                self.__buffer.task_done()
                self.__buffer_size.release()
        except queue.Empty:    pass

    def cancel(self, track: Track):
        if track is self.__active:
            return self.skip()
        if track in self.__tracks:
            self.__tracks.remove(track)
            track._fut.set_result(Status.CLEAR)

    def __len__(self) -> int:
        return len(self.__tracks)
