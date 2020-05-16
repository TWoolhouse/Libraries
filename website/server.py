import asyncio
from interface import Interface
import urllib.parse
from http import HTTPStatus as Status
from http.cookies import SimpleCookie as Cookie
from .buffer import Buffer
from . import error

import traceback

class Cookie(Cookie):

    def value(self, key: str):
        try:
            return self.__getitem__(key).value
        except KeyError:
            return None

class Session:
    def __init__(self, id: str):
        self.id = id

class Sessions:
    def __init__(self, new=Session):
        self.__new = new
        self.__container = {}

    def __getitem__(self, key: str) -> Session:
        try:
            return self.__container[key]
        except KeyError:
            session = self.__new(key)
            self.__container[session.id] = session
            return session
    def __delitem__(self, key: str):
        self.__container.__delitem__(key)

class Header:
    def __init__(self, name: str, *values: str):
        self.name = name.title().replace(" ", "-")
        self.values = list(values)

    @property
    def value(self):
        return self.values[0]
    @value.setter
    def value(self, value):
        self.values[0] = value

    def __repr__(self) -> str:
        return f"{self.name}<{', '.join(map(str, self.values))}>"

    def _format(self) -> str:
        return f"{self.name.title().replace(' ', '-')}: {'; '.join(map(str, self.values))}"

class HeaderContainer:

    def __init__(self):
        self.__container = {}

    def __getitem__(self, key) -> Header:
        return self.__container[key.title().replace(" ", "-")]

    def __setitem__(self, key, value: Header):
        assert isinstance(value, Header), f"'{self.__class__.__name__}' Can only Store '{Header.__name__}'"
        self.__container[key.title().replace(" ", "-")] = value

    def __delitem__(self, key):
        return self.__container.__delitem__(key.title().replace(" ", "-"))

    def __iter__(self):
        yield from self.__container.items()

    def get(self, key) -> Header:
        return self.__getitem__(key)
    def set(self, key, value) -> Header:
        return self.__setitem__(key, value)
    def pop(self, key):
        return self.__delitem__(key)

    def __lshift__(self, header: Header) -> "HeaderContainer":
        self.__setitem__(header.name, header)
        return self

    def _format(self):
        return "\r\n".join(head._format() for head in self.__container.values())

class BufferContainer:

    def __init__(self):
        self.__container = []

    def __lshift__(self, buffer: Buffer) -> "BufferContainer":
        self.__container.append(buffer)
        return self

    async def _compile(self, client) -> bytes:
        final = bytes()
        for buffer in self.__container:
            if isinstance(buffer, Buffer):
                try:
                    buffer = await buffer.compile()
                except error.BufferRead:
                    client.status = Status.NOT_FOUND
                    break
            elif isinstance(buffer, bytes):
                pass
            elif isinstance(buffer, str):
                buffer = buff.encode("utf-8")
            else:
                continue
            final += buffer

        return final

class Client:

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: str, port: int, command: str, query: dict, request: {str, Header}, cookies: Cookie):
        self.__reader, self._writer = reader, writer
        self.host, self.port = addr, port
        self.command, self.query, self.request, self.cookie = command, query, request, cookies
        self.status = Status.OK
        self.header = HeaderContainer()
        self.buffer = BufferContainer()
        self.session = Session(None)

class Request:

    def __init__(self, client: Client, request: list, seg: int, *args, **kwargs):
        self.client = client
        self.request = request
        self.seg = seg
        self.init(*args, **kwargs)

    def init(self, *args, **kwargs):
        pass

    async def handle(self) -> "Request":
        pass

class Tree:
    def __init__(self, blank__: Request=None, end__=error.TreeTraversal, default__=error.TreeTraversal, **dirs):
        self.__tree = {
            "": blank__,
        }
        for k,v in dirs.items():
            if isinstance(v, dict):
                v = Tree(**v)
            if isinstance(v, (Tree, Request, Exception)) or callable(v):
                tree = v
            self.__tree[k] = tree
        self.end = end__
        self.default = default__

    def traverse(self, request: list, segment: int, client: Client) -> Request:
        try:
            req = request[segment]
            segment += 1
            req = self.__tree[req]
        except IndexError as e:
            if issubclass(self.end, Exception):
                raise self.end(self, request, segment) from None
            return self.end(client, request, segment)
        except KeyError as e:
            if issubclass(self.default, Exception):
                raise self.default(self, request, segment, req) from None
            return self.default(client, request, segment)
        if isinstance(req, Tree):
            return req.traverse(request, segment, client)
        elif issubclass(req, Request):
            return req(client, request, segment)
        elif issubclass(req, Exception):
            raise req()
        else:
            return req()

class Server:

    def __init__(self, request: Request, port: int=80, host: str=None, client: type(Client)=Client):
        self.request = request
        self.client = client
        self.host, self.port = host, port

    async def serve(self):
        self.__server = await asyncio.start_server(self.__create_client, self.host, self.port)

        async with self.__server:
            await self.__server.serve_forever()

    async def __create_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        try:
            # Get First Line of the Request
            request = (await reader.readline()).decode().strip()
            # print("Request:", request)

            try:
                command, url, version = request.split()
            except ValueError:    return
            url = urllib.parse.urlparse(url)
            path = url.path or "/"
            query = dict(map(urllib.parse.unquote, q.split("=", 1)) for q in url.query.split("&")) if url.query else {}

            # Parse Headers
            headers = {}
            while (line := (await reader.readline()).decode().strip()):
                name, values = map(str.strip, line.split(":", 1))
                headers[name.lower()] = Header(name, values)

            # Read body
            if "content-length" in headers:
                body = (await reader.read(int(headers["content-length"].value)+1)).decode().strip()
                if body:
                    query.update(map(urllib.parse.unquote, q.split("=", 1)) for q in body.split("&"))

            # Parse Cookies
            cookies = Cookie()
            if "cookie" in headers:
                for cookie in headers["cookie"].value.split(";"):
                    name, value = cookie.strip().split("=")
                    cookies[name] = value

            # print(command, url.hostname, path)
            # print(query)
            # print(headers)
            # print(cookies)
            client = self.client(reader, writer, *addr, command, query, path, cookies)
            request = self.request(client, path.split("/")[1:], 0)

            # print("Request Handler")
            while isinstance(request, Request):
                # print(f"Proc Req: {type(request).__qualname__} {request}")
                request = await request.handle()
            # print("Request Handled")

            # Compile Client Buffer
            cbuffer = await client.buffer._compile(client)

            buffer = "\r\n".join(filter(None, (
                f"HTTP/1.1 {client.status.value} {client.status.phrase}",
                client.header._format(),
                client.cookie.output(),
            ))).strip() + "\r\n\r\n"

            writer.write(buffer.encode())
            writer.write(cbuffer.strip())
        except Exception as e:
            print("Connection:", "".join(traceback.format_exception(e, e, e.__traceback__)))
        finally:
            await writer.drain()
            writer.close()
