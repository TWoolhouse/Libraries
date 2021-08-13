import io
import collections
import numpy as np

class Stream(io.BufferedIOBase):
    def __init__(self, blocksize=4096):
        super().__init__()
        self._closed = False
        self._blocksize = blocksize
        self._index = 0
        self._data = collections.deque()

    def __len__(self) -> int:
        return self._data.__len__()

    def close(self):
        if not self._closed:
            self._closed = True
    @property
    def closed(self) -> bool:
        return self._closed

    def detach(self):
        raise io.UnsupportedOperation()
    def fileno(self) -> int:
        raise io.UnsupportedOperation(f"{self} has no file descriptor")
    def flush(self):
        return
    def isatty(self):
        return False

    def _read_blocks(self, size: int) -> list:
        if size < 0:
            size = self._blocksize * len(self._data)

        diff = size
        blocks = []

        while diff > 0:
            if not self._data:
                break

            block = self._data[0][self._index:]

            if len(block) > diff:
                block = block[:diff]

            self._index += len(block)
            if self._index == len(self._data[0]):
                self._index = 0
                self._data.popleft()

            diff -= len(block)
            blocks.append(block)
        return blocks

    def read(self, size=-1) -> bytes:
        if size == 0:
            return b""

        return b"".join(self._read_blocks(size))

    read1 = read
    def readable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int=io.SEEK_SET) -> int:
        if whence != io.SEEK_CUR:
            raise io.UnsupportedOperation("Can only seek from Current position")
        if offset < 0:
            raise io.UnsupportedOperation("Can only seek forwards")
        self.read(offset)
        return 0

    def seekable(self) -> bool:
        return False
    def tell(self) -> int:
        return 0
    def truncate(self, size: int=0) -> int:
        if size != 0:
            raise io.UnsupportedOperation("Can only Truncate to 0 bytes")
        self._data.clear()
        self._index = 0
        return 0

    def writable(self) -> bool:
        return True

    def write(self, buffer: bytes):
        index = 0
        size = len(buffer)
        while index < size:
            block = bytes(buffer[index:index+self._blocksize])
            index += len(block)
            self._data.append(block)

class StreamArray(Stream):

    def __init__(self, blocksize=4096, shape=(1,), dtype=None):
        super().__init__(blocksize)
        self._shape = shape
        self._dtype = dtype

    def read(self, size=-1) -> np.ndarray:
        if size == 0:
            return np.zeros((0, *self._shape[1:]), dtype=self._dtype)

        blocks = self._read_blocks(size)
        if blocks:
            return np.concatenate(blocks)
        return self.read(0)

    def write(self, buffer: np.ndarray):
        index = 0
        size = len(buffer)
        while index < size:
            block = buffer[index:index+self._blocksize]
            index += len(block)
            self._data.append(block)
