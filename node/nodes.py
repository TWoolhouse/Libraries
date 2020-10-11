import asyncio
from interface import Interface
from .data import Data, Tag
from typing import Union, Type
from collections import defaultdict

__all__ = ["Server", "Client"]

class Node:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.__open = True
        self.__reader, self.__writer = reader, writer
        self.__read_loop = Interface.schedule(self.__read_loop())
        self.__read = defaultdict(set)

    def __bool__(self) -> bool:
        return self.__open

    @Interface.submit
    async def __read_loop(self):
        data = await self.__reader.readuntil(b"<#>")
        if data:
            Interface.schedule(self.__process_data(data))

    @__read_loop.exit
    async def close(self):
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
            self._read[pre].add(data)

    async def _write(self, data: Data):
        head = "|".join(data.head).encode("utf8")
        tag = "|".join(data.tag).encode("utf8")
        payload = data.data if isinstance(data.data, bytes) else data.data.encode("utf8")
        self.__writer.write(head+b"<|>"+tag+b"<|>"+payload)
        await self.__writer.drain()

    async def _read(self, *prefix: Union[str, Tag]) -> [Data]:
        match = []
        for packet in self.__read[prefix[0]]:
            if all(pre in (*packet.head, *packet.tag) for pre in prefix[1:]):
                match.append(packet)
        for packet in match:
            for pre in (*packet.head, *packet.tag):
                self.__read[pre].discard(packet)
        return match

class DataInterface:

    def send(self, data: Union[Data, str, bytes], *head: Union[str, bytes, Tag]) -> bool:
        if not isinstance(data, Data):
            data = Data(data, *head)
        Interface.schedule(self._node._write(data))

    async def recv(self, wait: bool, *prefix: Union[str, Tag]) -> [Data]:
        match = []
        while len(match) < wait:
            match.extend(await self._node._read(*prefix))
        match.extend(await self._node._read(*prefix))

class Client(DataInterface):
    def __init__(self, addr: str, port: int, *dispatch: Dispatcher):
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

    async def __aenter__(self):
        await self.open()
        return self
    def __aexit__(self, *args):
        return self.close()

class SClient(DataInterface):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._node = Node(reader, writer)

    async def close(self):
        await self._node.close()

class Server:

    def __init__(self, addr: str, port: int, *dispatch: Dispatcher, limit: int=100, encrypt=False, client: Type[SClient]=SClient):
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
        x = self.client(reader, writer)

    def close(self, all=False):
        self.__server.close()
