import asyncio
import threading
import numpy as np
import sounddevice as sd
from .base import Properties, Status
from .stream import Mixer, Buffer, TS
from stream import StreamArray
from interface import Interface

class ControllerMixer(Mixer):
    def __init__(self):
        super().__init__()
        self.buffer: Buffer

    async def open(self, properties: Properties):
        if not self.prop:
            await super().open(properties)
            self.buffer = Buffer(self, self.prop.size, self.prop.blocks)
            await self.buffer.open(self.prop)

    def read_next(self, size: int) -> np.ndarray:
        data = self.buffer._read_raw(size)
        Interface.loop.call_soon_threadsafe(self.buffer._counter_control)
        return data

    def start(self, properties: Properties) -> asyncio.Future:
        return Interface.schedule(self.open(properties))

class Controller:

    def __init__(self, blocks: int=8, size: int=8192):
        fmt_types = {"float32": "f32le"}

        self._driver = sd.OutputStream(dtype="float32", callback=self._stream_callback)
        self.properties = Properties(
            self._driver.dtype,
            fmt_types[self._driver.dtype],
            int(self._driver.channels),
            int(self._driver.samplerate),
            size, blocks
        )
        Interface.terminate.schedule(self._driver.close)
        self._stream = ControllerMixer()

    def _stream_callback(self, outdata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags):
        data = self._stream.read_next(frames)
        ln = len(data)
        outdata[:ln] = data
        outdata[ln:].fill(0)

    def play(self):
        """Begin audio processing"""
        if not self._driver.active:
            self._stream.start(self.properties).add_done_callback(lambda fut: (fut.result(), self._driver.start()))
    def pause(self):
        """Stop audio processing"""
        self._driver.stop()

    def include(self, stream: TS, pop: bool=True) -> TS:
        """Add a stream to the mixer"""
        return self._stream.add(stream, pop)
