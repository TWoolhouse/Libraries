from .controller import Track, Properties, Status
from .ffmpeg import FFmpeg
import io
import asyncio
import numpy as np
import soundfile as sf
from typing import Union, BinaryIO

class Chunk:
    def __init__(self, name: str, data: int=1, offset: int=0, seek: int=0):
        self.name = name
        self.data = data
        self.offset = offset
        self.seek = seek
    def compile(self, properties: Properties):
        self.size = int(self.offset + self.data * properties.channels)

Type = {
"default": Chunk("default"),
"mp3": Chunk("mp3", 16, 32, 0),
}

class File(Track):

    def __init__(self, file: Union[str, BinaryIO], chunksize: Chunk=Type["default"]):
        super().__init__()
        if isinstance(file, io.IOBase):
            self.path: str = None
            self.file: BinaryIO = file
        else:
            self.info.source = file
            self.path: str = file
        self.chunk: Chunk = chunksize

    async def read(self, size: int) -> bytes:
        size *= self.chunk.size
        data = self.file.read(size)
        if len(data) < size:
            self.state.status.value = Status.DONE
        return data

    async def open(self):
        self.chunk.compile(self.properties)
        if self.path is not None:
            self.file = open(self.path, "rb")
        self.file.seek(self.chunk.seek)
        await super().open()
    async def close(self):
        await super().close()
        self.file.close()

class FileFast(Track):

    def __init__(self, file: Union[str, BinaryIO]):
        super().__init__()
        self.path: Union[str, BinaryIO] = file
        if isinstance(file, str):
            self.info.source = file

    async def read(self, size: int) -> np.ndarray:
        data = self.file.read(size, dtype=self.properties.dtype)
        if len(data) < size:
            self.state.status.value = Status.DONE
        return data

    async def open(self):
        self.file = sf.SoundFile(self.path)
        self.info.name = self.file.name
        self.info.duration = self.file.frames * self.file.samplerate
        await super().open()
    async def close(self):
        await super().close()
        self.file.close()

class FileCast(Track):

    def __init__(self, file: Union[str, BinaryIO], format: Union[Chunk, str]):
        super().__init__()
        if isinstance(file, io.IOBase):
            self.path: str = None
            self.file: BinaryIO = file
        else:
            self.info.source = file
            self.path: str = file
        self.format = format.name if isinstance(format, Chunk) else format
        self._ffmpeg = FFmpeg("{format} -i pipe: -vn -f wav -ac {channels} -ar {samplerate} pipe:")
        # self.mem = sf.SoundFile()

    async def read(self, size: int) -> np.ndarray:
        data = self.mem.read(size, dtype=self.properties.dtype)
        if len(data) < size:
            self.state.status.value = Status.DONE
        return data

    async def open(self):
        if self.path is not None:
            self.file = open(self.path, "rb")

        self._ffmpeg.compile(format=f"-f {self.format}" if self.format is not None else "" , channels=self.properties.channels, samplerate=self.properties.samplerate)
        self.mem = sf.SoundFile(io.BytesIO(await self._ffmpeg.call(self.file.read())))
        self.file.close()

        self.info.name = self.mem.name
        self.info.duration = self.mem.frames * self.mem.samplerate

        await super().open()

    async def close(self):
        pass
