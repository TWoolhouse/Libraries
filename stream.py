import io
import collections

class Stream(io.BufferedIOBase):
    def __init__(self, blocksize=4096):
        super().__init__()
        self.__closed = False
        self._blocksize = blocksize
        self.__index = 0
        self.__data = collections.deque()

    def close(self):
        if not self.__closed:
            self.__closed = True
    @property
    def closed(self) -> bool:
        return self.__closed

    def detach(self):
        raise io.UnsupportedOperation()
    def fileno(self) -> int:
        raise io.UnsupportedOperation(f"{self} has no file descriptor")
    def flush(self):
        return
    def isatty(self):
        return False

    def read(self, size=-1) -> bytes:
        if size == 0:
            return b""

        if size < 0:
            size = self._blocksize * len(self.__data)

        diff = size
        blocks = []

        while diff > 0:
            if not self.__data:
                break

            block = self.__data[0][self.__index:]

            if len(block) > diff:
                block = block[:diff]

            self.__index += len(block)
            if self.__index == len(self.__data[0]):
                self.__index = 0
                self.__data.popleft()

            diff -= len(block)
            blocks.append(block)

        return b"".join(blocks)

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
        self.__data.clear()
        self.__index = 0
        return 0

    def writable(self) -> bool:
        return True

    def write(self, buffer: bytes):
        index = 0
        size = len(buffer)
        while index < size:
            block = bytes(buffer[index:index+self._blocksize])
            index += len(block)
            self.__data.append(block)
