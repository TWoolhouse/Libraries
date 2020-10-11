import asyncio
from interface import Interface
from .data import Data, Tag
from typing import Union, Type, Tuple
from collections import defaultdict

__all__ = ["Server", "Client"]

class Node:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.__open = True
        self.__reader, self.__writer = reader, writer
        self.__read_loop = self.__read_loop(self)
        self.__read = defaultdict(set)

    def __bool__(self) -> bool:
        return self.__open

    @Interface.Repeat
    async def __read_loop(self):
        try:
            data = await self.__reader.readuntil(b"<#>")
        except asyncio.exceptions.IncompleteReadError as e:
            return True
        if data:
            Interface.schedule(self.__process_data(data[:-3]))

    @__read_loop.exit
    async def close(self):
        # print("Close:", self)
        self.__open = False
        self.__read_loop.cancel()
        self.__writer.close()
        await self.__writer.wait_closed()

    async def __process_data(self, data: bytes):
        head, tag, payload = data.split(b"<|>")
        head = head.decode("utf8").split("|")
        tag = tag.decode("utf8").split("|")
        if "BIN" not in head:
            payload = payload.decode("utf8")
        data = Data(payload, *head, *map(Tag, tag))
        for pre in (*data.head, *data.tag):
            self.__read[pre].add(data)

    async def _write(self, data: Data):
        head = "|".join(data.head).encode("utf8")
        tag = "|".join(map(str, data.tag)).encode("utf8")
        payload = data.data if isinstance(data.data, bytes) else data.data.encode("utf8")
        self.__writer.write(head+b"<|>"+tag+b"<|>"+payload+b"<#>")
        try:
            await self.__writer.drain()
        except ConnectionError:
            await self.close()
        return True

    def _read(self, *prefix: Union[str, Tag]) -> Tuple[Data]:
        match = []
        for packet in self.__read[prefix[0]]:
            if all(pre in (*packet.head, *packet.tag) for pre in prefix[1:]):
                match.append(packet)
        for packet in match:
            for pre in (*packet.head, *packet.tag):
                self.__read[pre].discard(packet)
        return match

class DataInterface:

    def send(self, data: Union[Data, str, bytes], *head: Union[str, bytes, Tag]) -> asyncio.Future:
        if not isinstance(data, Data):
            data = Data(data, *head)
        return Interface.schedule(self._node._write(data))

    async def recv(self, wait: bool, *prefix: Union[str, Tag]) -> Tuple[Data]:
        match = []
        match.extend(self._node._read(*prefix))
        while len(match) < wait:
            await Interface.next()
            match.extend(self._node._read(*prefix))
        return match

class Client(DataInterface):
    def __init__(self, addr: str, port: int, *dispatch: 'Dispatcher'):
        self.addr, self.port = addr, port
        self.dispatchers = {}
        self._node = None

    async def open(self) -> bool:
        if not self._node:
            self._node = Node(*await asyncio.open_connection(self.addr, self.port))
        return True
    async def close(self) -> bool:
        await self._node.close()
        return True

    def __enter__(self) -> 'Client':
        raise NotImplementedError
        return self

    async def __aenter__(self) -> 'Client':
        await self.open()
        return self
    def __aexit__(self, *args):
        return self.close()

class SClient(DataInterface):

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._node = Node(reader, writer)
        self.init()
        if self.anit is not self.__anit:
            Interface.schedule(self.anit())

    def init(self):
        pass
    async def __anit(self):
        pass
    anit = __anit

    async def close(self):
        await self._node.close()

class Server:

    def __init__(self, addr: str, port: int, *dispatch: 'Dispatcher', limit: int=100, encrypt=False, client: Type[SClient]=SClient):
        self.addr, self.port = addr, port
        self.limit = limit
        self.client = client
        self.dispatchers = {}
        self.__server = None
        self.__connections = {}

    async def serve(self):
        self.__server = await asyncio.start_server(self.__create_client, self.addr, self.port, backlog=self.limit)
        async with self.__server:
            await self.__server.serve_forever()

    async def __create_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        c = self.client(reader, writer)
        self.__connections[addr[1]] = c
        # print("Connection:", c)

    def close(self, all=False):
        self.__server.close()
