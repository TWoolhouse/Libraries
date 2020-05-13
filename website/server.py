import asyncio
from interface import Interface
import urllib.parse
from http import HTTPStatus
from http.cookies import BaseCookie as Cookie
from .buffer import Buffer

import traceback

class Header:
    def __init__(self, name: str, *values: str):
        self.name = name
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
        return f"{self.name}: {'; '.join(map(str, self.values))}"

class Client:

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: str, port: int, command: str, query: dict, request: {str, Header}, cookies: Cookie):
        self.__reader, self._writer = reader, writer
        self.host, self.port = addr, port
        self.command, self.query, self.request, self.cookie = command, query, request, cookies
        self.status = HTTPStatus.OK
        self.header = {}
        self.buffer = []

class Request:

    def __init__(self, client: Client, request: list, seg: int):
        self.client = client
        self.request = request
        self.seg = seg
        self.init()

    def init(self):
        pass

    async def handle(self) -> "Request":
        pass

class Tree:
    def __init__(self, blank__: Request=None, default__=ValueError, **dirs):
        self.__tree = {
            "": blank__,
        }
        for k,v in dirs.items():
            if isinstance(v, dict):
                v = Tree(**v)
            if isinstance(v, (Tree, Request, Exception)) or callable(v):
                tree = v
            self.__tree[k] = tree
        self.default = default__

    def traverse(self, request: list, segment: int, client: Client) -> Request:
        try:
            req = request[segment]
            segment += 1
            req = self.__tree[req]
        except IndexError as e:
            if issubclass(self.default, Exception):
                raise self.default(request, segment) from e
            return self.default(request, segment)
        except KeyError as e:
            if issubclass(self.default, Exception):
                raise self.default(req) from e
            return self.default(request, segment)
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

            command, url, version = request.split()
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

            buffer = "\r\n".join((
                f"HTTP/1.1 {client.status.value} {client.status.phrase}",
                "\r\n".join(h._format() for h in client.header.values()), 
                client.cookie.output(),
            )).strip() + "\r\n\r\n"

            # print(buffer.encode())
            # print(client.buffer)

            # Compile Client Buffer
            cbuffer = bytes()
            for buff in client.buffer:
                if isinstance(buff, Buffer):
                    buff = await buff._compile()
                elif isinstance(buff, str):
                    buff = buff.encode()
                else:
                    continue
                cbuffer += buff

            writer.write(buffer.encode())
            writer.write(cbuffer.strip())
        except Exception as e:
            print("Connection:", "".join(traceback.format_exception(e, e, e.__traceback__)))
        finally:
            await writer.drain()
            writer.close()
