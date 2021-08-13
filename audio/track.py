from .base import Track, Stream, Status, Properties, NodeMeta
import soundfile
import numpy as np
import io
from tinytag import TinyTag as tt
from stream import StreamArray
from typing import Union, BinaryIO

class Loader(Track):

    def __init__(self, stream: Track):
        super().__init__()
        self.stream = stream
        self.buffer: StreamArray

    async def open(self, properties: Properties):
        """Open the Gate before reading / processing can occur"""
        await super().open(properties)
        self.buffer = StreamArray(self.prop.size, (self.prop.size, self.prop.channels), self.prop.dtype)

        self.stream.status.set(Status.PREPARE)
        await self.stream.open(properties)
        self.info = self.stream.info
        self.proc.chain = [*self.stream.proc.chain, *self.proc.chain]
        self.proc.io[0], self.proc.io[1] = self.stream.proc.io[0], np.ndarray
        self.proc.open(self.prop)
        self.stream.status.set(Status.ACTIVE)

        while self.stream.status._val < Status.DONE:
            self.buffer.write(await self.stream.process(self.prop.size))

        data = self.buffer.read()
        self.buffer.write(await self.proc.execute(data, len(data)))
        self.proc.chain.clear()
        self.proc.open(self.prop)

    async def close(self):
        """Closes the Gate after all reading / processing has finished"""
        await self.stream.close()
        await super().close()

    async def read(self, size: int) -> np.ndarray:
        """Read previous Track/Stream's processed data"""
        data = self.buffer.read(size)
        if len(data) < size:
            self.status.set(Status.DONE)
        return data

class PreLoadMeta(NodeMeta):
    def __call__(self, *args, preload=False, **kwargs):
        obj = super().__call__(*args, **kwargs)
        if preload:
            return Loader(obj)
        return obj

class PreLoad(Track, metaclass=PreLoadMeta):
    def __init__(self, preload=False):
        super().__init__()

class File(PreLoad):

    def __init__(self, filename: Union[str, bytes, int, BinaryIO], seek: float=0, preload=False):
        super().__init__(preload=preload)
        self.filename = filename
        self._seek = max(0, seek)

    async def open(self, properties: Properties):
        """Open the track before reading / processing can occur"""
        await super().open(properties)
        try:
            self.file = soundfile.SoundFile(self.filename)
            self.info.name = self.file.name
            self.info.source = self.filename
            self.info.duration = self.file.frames

            if self._seek:
                self.file.seek(int(self.prop.samplerate * self._seek))
        except RuntimeError as exc_sf:
            raise

    async def close(self):
        await super().close()
        self.file.close()

    async def read(self, size: int) -> np.ndarray:
        data = self.file.read(size, self.prop.dtype)
        if len(data) < size:
            self.status.set(Status.DONE)
        return data

class Raw(PreLoad):
    def __init__(self, filename: Union[str, int, BinaryIO], preload=False):
        super().__init__(preload=preload)
        self.filename = filename
    async def open(self, properties: Properties):
        await super().open(properties)
        if isinstance(self.filename, (str, int)): # File
            self.file = open(self.filename, "rb")
            self.info.source = self.filename
        else: # File-like
            self.file = self.filename
            self.info.source = type(self.filename)
