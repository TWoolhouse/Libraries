import io
from typing import IO
from .base import TrackBase

class TrackRawFile(TrackBase):
    def __init__(self, file: IO, close=True):
        super().__init__()
        self.file = file
        self._close_file = close

    async def _read(self, size: int) -> list:
        return self.file.read(size * self._size)

    async def _preload(self, stream: 'sd.RawOutputStream'):
        self._size = stream.channels * stream.samplesize
        if not self.file.closed and self.file.readable():
            if self.file.seekable():
                pos = self.file.tell()
                self.file.seek(0, io.SEEK_END)
                self._duration_total = int(self.file.tell())
                self.file.seek(pos)
        else:
            raise ValueError

    async def _close(self):
        await super()._close()
        if self.file is not None and not self.file.closed and self._close_file:
            self.file.close()
