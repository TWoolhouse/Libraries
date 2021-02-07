from .controller import Processor
from .ffmpeg import FFmpeg
import asyncio
import numpy as np
import functools

class Format(Processor):

    BLOCKSIZE = 32768

    def __init__(self, ftype: str, otype: str="f32le"):
        super().__init__()
        self.ifile_type, self.ofile_type = ftype, otype
        self._ffmpeg = FFmpeg("-f {itype} -i pipe: -vn -f {otype} -ac {channels} -ar {samplerate} pipe:")

    def _bind(self, properties):
        super()._bind(properties)
        self._ffmpeg.compile(
            itype=self.ifile_type,
            otype=self.ofile_type,
            channels=self.properties.channels,
            samplerate=self.properties.samplerate
        )

    async def process(self, data: bytes, size: int) -> bytes:
        return await self._ffmpeg.call(data)

class Speed(Processor):

    BLOCKSIZE = 32768

    def __init__(self, fraction: float, irate: int=None, orate: int=None):
        super().__init__()
        self.irate, self.orate = irate, orate
        self.fraction = fraction
        self._ffmpeg = FFmpeg("-f f32le -ac {channels} -ar {irate} -i pipe: -vn -f f32le -ac {channels} -ar {orate} pipe:")

    def _bind(self, properties):
        super()._bind(properties)
        self._ffmpeg.compile(
            irate=int((self.properties.samplerate if self.irate is None else self.irate) * self.fraction),
            orate=self.properties.samplerate if self.orate is None else self.orate,
            channels=self.properties.channels,
        )

    async def process(self, data: bytes, size: int) -> bytes:
        return await self._ffmpeg.call(data)

class Volume(Processor):

    def __init__(self, fraction: float):
        self.fraction = fraction

    async def process(self, data: np.ndarray, size: int) -> np.ndarray:
        return data * self.fraction
