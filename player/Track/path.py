import io
import soundfile as sf
from .base import TrackBase

class TrackPathFile(TrackBase):
    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._file = None

    async def _read(self, size: int) -> list:
        return self._file.buffer_read(size, self._format)

    async def _preload(self, stream: 'sd.RawOutputStream'):
        self._format = stream.dtype
        self._file = sf.SoundFile(self.path)
        self._duration_total = int(self._file.frames)
    async def _close(self):
        super()._close()
        if self._file is not None:
            self._file.close()

    def copy(self):
        if isinstance(self.path, str):
            return self.__class__(self.path)
        elif isinstance(self.path, io.IOBase):
            try:
                self.path.seek(0, io.SEEK_SET)
            except io.UnsupportedOperation as e:
                raise NotImplementedError from e
        super().copy()
