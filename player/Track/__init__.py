import io
import http
import asyio
import socket
from ..Status import Status
from typing import overload, IO, Union

from .base import TrackBase
from .path import TrackPathFile
from .file_io import TrackRawFile
from .protocol import TrackStream

class Track:

    def __new__(cls, arg, *args, raw=False, **kwargs):
        if isinstance(arg, str):
            return TrackPathFile(arg, *args, **kwargs)
        elif isinstance(arg, (http.client.HTTPResponse, asyio.Request, socket.socket)):
            return TrackStream(arg, *args, **kwargs)
        elif isinstance(arg, io.IOBase):
            if raw:
                return TrackRawFile(arg, *args, **kwargs)
            return TrackPathFile(arg, *args, **kwargs)
        # if isinstance()
        return super().__new__(cls)

    @overload
    def __init__(self, path: str): ...
    @overload
    def __init__(self, stream: IO, raw=False): ...
    @overload
    def __init__(self, socket: Union[http.client.HTTPResponse, asyio.Request, socket.socket]): ...

    def __init__(self, path: str):
        self.status: Status = Status
        raise NotImplementedError
    def __await__(self):
        return self.wait().__await__()

    @overload
    def duration(self, type="f") -> int: ...
    @overload
    def duration(self, type="s") -> float: ...
    @overload
    def duration(self, type="%") -> float: ...

    @overload
    def duration_total(self, type="f") -> int: ...
    @overload
    def duration_total(self, type="s") -> float: ...

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
