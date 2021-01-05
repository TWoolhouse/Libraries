import asyio
import asyncio
from interface import Interface
from .data import Data, Tag
from typing import Union, Type, Tuple, Callable, Any
from collections import defaultdict
import debug

__all__ = ["Server", "Client"]

TIMEOUT = 100

class Node:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.__open = True
        self.__reader, self.__writer = reader, writer
        self._read_loop = self._read_loop(self)
        self._buffer = defaultdict(set)
        self._queue = asyio.Counter()

    def __repr__(self) -> str:
        addr = self.__writer.get_extra_info("peername")
        return f"<{'O' if self.__open else 'X'} {addr[0]}:{addr[1]}>"

    def __bool__(self) -> bool:
        return self.__open

    async def wait(self):
        self._queue.wait()

    @Interface.Repeat
    async def _read_loop(self):
        try:
            data = await asyncio.wait_for(self.__reader.readuntil(b"<#>"), TIMEOUT)
        except asyncio.exceptions.IncompleteReadError as e:
            return True
        except ConnectionError as e:
            return True
        except asyncio.TimeoutError as e:
            return True
        if data:
            Interface.schedule(self._process_data(data[:-3]))

    @_read_loop.exit
    async def close(self):
        self.__open = False
        self._read_loop.cancel()
        self.__writer.close()
        try:
            await self.__writer.wait_closed()
        except ConnectionError:
            pass

    async def _dispatch(self, data: Data) -> bool:
        return True

    async def _process_data(self, data: bytes):
        head, tag, payload = data.split(b"|")
        head = head.decode("utf8").split("!")
        dtype, head = head[0], head[1:]
        tag = tag.decode("utf8").split("!")
        data = Data(payload, *head, *map(Tag, filter(None, tag)))
        data.data = data._decode(dtype)
        proc_data = await self._dispatch(data)
        if proc_data:
            for pre in (*data.head, *data.tag):
                if pre:
                    self._buffer[pre].add(data)

    async def _write(self, data: Data):
        dtype, payload = data._encode()
        head = "!".join([dtype]+data.head).encode("utf8")
        tag = "!".join(map(str, data.tag)).encode("utf8")
        block = head+b"|"+tag+b"|"+payload+b"<#>"
        # print(block)
        self.__writer.write(block)
        try:
            await self.__writer.drain()
            self._queue.decr()
        except ConnectionError:
            self._queue.decr()
            await self.close()
        return True

    def _read(self, *prefix: Union[str, Tag]) -> Tuple[Data]:
        match = []
        for packet in self._buffer[prefix[0]]:
            if all(pre in (*packet.head, *packet.tag) for pre in prefix[1:]):
                match.append(packet)
        for packet in match:
            for pre in (*packet.head, *packet.tag):
                self._buffer[pre].discard(packet)
        return match

class DataInterface:

    __DISPATCH_PREFIX = "dsptch_"

    def __init__(self, dispatchers: dict[str, Callable[['DataInterface', Data], Any]]):
        self.dispatchers = {k.upper(): v for k,v in dispatchers.items()} | {k[len(self.__DISPATCH_PREFIX):].upper(): getattr(self.__class__, k) for k in dir(self) if k.startswith(self.__DISPATCH_PREFIX)}

    def send(self, data: Union[Data, str, bytes], *head: Union[str, bytes, Tag]) -> asyncio.Future:
        if not isinstance(data, Data):
            if not head:
                raise ValueError("Need atleast one header")
            data = Data(data, *head)
        self._node._queue.incr()
        return Interface.schedule(self._node._write(data))

    async def recv(self, *prefix: Union[str, Tag], wait: bool=True) -> Tuple[Data]:
        prefix = [p if isinstance(p, Tag) else p.upper() for p in prefix]
        match = []
        match.extend(self._node._read(*prefix))
        while len(match) < wait:
            if not (self._node or self._node is None):
                return None
            await Interface.next()
            match.extend(self._node._read(*prefix))
        return match

    async def wait(self):
        await self._node._queue.wait()

    async def close(self) -> bool:
        if self._node is None:
            return False
        await self._node._queue.wait()
        await self._node.close()
        await self._node._read_loop.wait()
        return True

    async def open(self):
        self._node._dispatch = self._dispatch
        async def close_callback():
            await self._node._read_loop.wait()
            await self.close()
        Interface.schedule(close_callback())

    async def _dispatch(self, data: Data) -> bool:
        for prefix in data.head:
            if f := self.dispatchers.get(prefix, False):
                if await Interface.schedule(f, self, data):
                    break
        else:
            return True
        return False

Dispatch = Callable[[DataInterface, Data], Any]

class Client(DataInterface):
    def __init__(self, addr: str, port: int, **dispatch: Dispatch):
        super().__init__(dispatch)
        self.addr, self.port = addr, port
        self._node = None

    async def open(self) -> bool:
        if not self._node:
            self._node = Node(*await asyncio.open_connection(self.addr, self.port))
            await super().open()
            return True
        return False

    def __enter__(self) -> 'Client':
        raise NotImplementedError
        return self

    async def __aenter__(self) -> 'Client':
        await self.open()
        return self
    async def __aexit__(self, *args):
        return await self.close()

class SClient(DataInterface):

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, dispatchers: dict[str, Dispatch], server: 'Server'):
        super().__init__(dispatchers)
        self._node = Node(reader, writer)
        self.server: Server = server

    async def close(self):
        await super().close()
        self.server.connections.pop(self, None)

class Server:

    def __init__(self, addr: str, port: int, limit: int=100, encrypt=False, client: Type[SClient]=SClient, **dispatch: Dispatch):
        self.addr, self.port = addr, port
        self.limit = limit
        self.client = client
        self.dispatchers = dispatch
        self.__server = None
        self.__open = False
        self.__wait = asyncio.Event()
        self.connections: dict[SClient, tuple] = {}

    def __bool__(self):
        return self.__open

    async def __serve(self, fut):
        async with self.__server:
            fut.set_result(True)
            await self.__server.serve_forever()

    async def serve(self):
        if self.__open:
            return
        self.__open = True
        self.__wait.clear()
        self.__server = await asyncio.start_server(self.__create_client, self.addr, self.port, backlog=self.limit)
        fut = Interface.loop.create_future()
        Interface.schedule(self.__serve(fut))
        await fut

    async def __create_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        c = self.client(reader, writer, self.dispatchers, self)
        await c.open()
        self.connections[c] = addr

    def close(self, all=False):
        self.__server.close()
        self.__open = False
        self.__wait.set()

    async def wait(self):
        return await self.__wait.wait()

    def __enter__(self) -> 'Server':
        raise NotImplementedError
        return self

    async def __aenter__(self):
        await self.serve()
        return self
    async def __aexit__(self, *args):
        self.close()
        return
