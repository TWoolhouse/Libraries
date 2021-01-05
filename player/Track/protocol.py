import asyncio
import asyio
import http
import socket
from typing import Union
from stream import Stream
from .file_io import TrackRawFile
from interface import Interface

class TrackStream(TrackRawFile, asyncio.Protocol):

    FFMPEG = "D:/Programs/ffmpeg/bin/ffmpeg.exe"
    BUFFERSIZE = 8192

    def __init__(self, response: Union[http.client.HTTPResponse, asyio.Request, socket.socket]):
        self.stream = Stream()
        super().__init__(self.stream)
        self.response = response
        self.queue = asyncio.Queue()
        self.proc = f"{self.FFMPEG} -f mp3 -i pipe: -f f32le -ac {{}} -ar {{}} pipe:"
        self._recv_data = asyncio.Event()

    async def _read(self, size: int) -> list:
        s = size * self._size
        data = self.stream.read(s)
        while len(data) < s:
            self._recv_data.clear()
            await self._recv_data.wait()
            data += self.stream.read(s - len(data))
        return data

    async def _preload(self, stream: 'sd.RawOutputStream'):
        await super()._preload(stream)
        self.proc = self.proc.format(stream.channels, stream.samplerate)
        self._recv_size = self._size * self.BUFFERSIZE
        self.stream._blocksize = self._size
        Interface.schedule(self.__recv())

        if isinstance(self.response, socket.socket):
            sock = self.response
        elif isinstance(self.response, asyio.Request):
            sock = socket.fromfd((await self.response.wait()).fileno(), socket.AF_INET, socket.SOCK_STREAM)
        elif isinstance(self.response, http.client.HTTPResponse):
            sock = socket.fromfd(self.response.fileno(), socket.AF_INET, socket.SOCK_STREAM)
        self.transport, protocol = await Interface.loop.create_connection(lambda: self, sock=sock)
        await Interface.next()

    # def connection_made(self, transport):
    #     print("Starting Stream", transport)

    def data_received(self, data):
        self.queue.put_nowait(data)
    def connection_lost(self, exec):
        self.stream.close()

    async def __recv(self):
        while not self.stream.closed:
            data = b""
            while len(data) < self._recv_size:
                data += await self.queue.get()
            proc = await asyncio.create_subprocess_shell(self.proc, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            output = await proc.communicate(data)
            self.stream.write(output[0])
            self._recv_data.set()

    async def _close(self):
        if not self.transport.is_closing():
            self.transport.close()
        await super()._close()
