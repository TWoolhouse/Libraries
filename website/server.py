import debug
import asyncio
from interface import Interface
import socket
import ssl
import urllib.parse
from http import HTTPStatus as Status
from http.cookies import SimpleCookie as Cookie
from .buffer import Buffer
from . import error
from ._ssl import context as ssl_context
import functools
from typing import Type

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
    def __init__(self, name: str, *values: str, split="; "):
        self.name = name.title().replace(" ", "-")
        self.values = list(values)
        self.split = split

    @property
    def value(self):
        return self.values[0]
    @value.setter
    def value(self, value):
        self.values[0] = value

    def __repr__(self) -> str:
        return f"{self.name}<{', '.join(map(str, self.values))}>"

    def _format(self) -> str:
        return f"{self.name.title().replace(' ', '-')}: {self.split.join(map(str, self.values))}"

class HeaderContainer:

    def __init__(self):
        self.__container = {}

    def __getitem__(self, key) -> Header:
        return self.__container[key.title().replace(" ", "-")]

    def __setitem__(self, key, value: Header):
        assert isinstance(value, Header), f"'{self.__class__.__name__}' Can only Store '{Header.__name__}'"
        self.__container[key.title().replace(" ", "-")] = value
        return value

    def __delitem__(self, key):
        return self.__container.__delitem__(key.title().replace(" ", "-"))

    def __iter__(self):
        yield from self.__container.items()

    def get(self, key, default=None) -> Header:
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
    def set(self, key, value) -> Header:
        return self.__setitem__(key, value)
    def pop(self, key):
        return self.__delitem__(key)

    def __lshift__(self, header: Header) -> "HeaderContainer":
        self.__setitem__(header.name, header)
        return self

    def _format(self):
        return "\r\n".join(head._format() for head in self.__container.values())

    def __contains__(self, key: str) -> bool:
        return key.title().replace(" ", "-") in self.__container

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
                buffer = buffer.encode("utf-8")
            else:
                continue
            final += buffer

        return final

class Client:

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server, server_addr: str, peer_addr: str, peer_port: int, ssl: bool, command: str, path: str, query: dict, request: HeaderContainer, cookies: Cookie):
        self.__reader, self._writer = reader, writer
        self.peer, self.port = peer_addr, peer_port
        self.hostname = server_addr
        self.server = server
        self.ssl = ssl
        self.command, self.path, self.query, self.request, self.cookie = command, path, query, request, cookies
        self.status = Status.OK
        self.header = HeaderContainer()
        self.buffer = BufferContainer()
        self.session = Session(None)
        self.close = bool(self.request.get("Connection", "").value.lower() != "keep-alive")

class DefaultRequest:
    class __base:
        def __init__(self, client: Client, request: list, seg: int, *args, **kwargs):
            raise RuntimeError
    class ssl(__base):
        pass
    class redirect(__base):
        pass

class Request:

    default = DefaultRequest
    def __init__(self, client: Client, request: list, seg: int, *args, **kwargs):
        self.client = client
        self.request = request
        self.seg = seg
        self.init(*args, **kwargs)

    def __await__(self):
        return self.handle().__await__()

    def init(self, *args, **kwargs):
        pass

    async def handle(self) -> "Request":
        pass

    def secure(func):
        @functools.wraps(func)
        async def enforce_secure(self):
            if self.client.ssl:
                return await func(self)
            return self.default.ssl(self.client, self.request, self.seg)
        return enforce_secure

    def redirect(path=None, query=None, hostname=None, port=None, scheme="http"):
        class redirect(DefaultRequest.redirect):
            def init(self, *args, **kwargs):
                super().init(path, query, hostname, port, scheme)
        return redirect

class DefaultRequest:
    class redirect(Request):
        def init(self, path=None, query=None, hostname=None, port=None, scheme=None):
            self.path = path or "/".join(self.request)
            self.query = query
            self.hostname = hostname or self.client.hostname
            self.port = port or (self.client.server.https if self.client.ssl else self.client.server.http)
            self.scheme = scheme or ("https" if self.client.ssl else "http")
        async def handle(self):
            self.client.status = self.client.status.PERMANENT_REDIRECT
            self.client.header << Header("Location", f"{self.scheme}://{self.hostname}:{self.port}/{self.path}{f'?{self.query}' if self.query else ''}")
    class ssl(redirect):
        def init(self, *args, **kwargs):
            super().init("/".join(self.request), None, self.client.hostname, self.client.server.https, "https")
            # self.client.header << Header("Location", f"https://{self.client.hostname}:{self.client.server.https}/{'/'.join(self.request)}")

Request.default = DefaultRequest

class Tree:
    def __init__(self, blank__: Request=error.TreeTraversal, end__=error.TreeTraversal, default__=error.TreeTraversal, **dirs):
        self.__tree = {
            "": blank__,
        }
        for k,v in dirs.items():
            if isinstance(v, dict):
                v = Tree(**v)
            # if isinstance(v, (Tree, Request, Exception)) or callable(v):
            #     tree = v
            self.__tree[k] = v
        self.end = end__
        self.default = default__

    @debug.log
    def traverse(self, request: list, segment: int, client: Client, *args, **kwargs) -> Request:
        try:
            req = request[segment]
            segment += 1
            req = self.__tree[req]
        except IndexError as e:
            segment += 1
            if issubclass(self.end, Exception):
                raise self.end(self, request, segment) from None
            req = self.end
        except KeyError as e:
            if issubclass(self.default, Exception):
                raise self.default(self, request, segment, req) from None
            req = self.default
        if isinstance(req, Tree):
            return req.traverse(request, segment, client, *args, **kwargs)
        elif isinstance(req, type):
            if issubclass(req, Request):
                return req(client, request, segment, *args, **kwargs)
            elif issubclass(req, Exception):
                raise req(self, request, segment)
        elif isinstance(req, Buffer):
            client.buffer << req
            return req
        elif callable(req):
            return req(*args, **kwargs)
        else:
            return req

    def insert(self, key: str, item) -> "Tree":
        if isinstance(item, dict):
            item = Tree(**item)
        self.__tree[key] = item

class Server:

    class Data:
        def __init__(self, http: int, https: int):
            self.http, self.https = http, https

    def __init__(self, request: Type[Request], port: int=80, host: str="", client: Type[Client]=Client, ssl: int=None):
        self.request = request
        self.client = client
        self.host, self.port = host, port
        self.ssl = ssl
        self.data = Server.Data(self.port, self.ssl)

    async def serve(self):
        debug.print(f"Opening Server: {self.port}{' && {}'.format(self.ssl) if self.ssl else ''}")
        self.__server = await asyncio.start_server(self.__create_client, self.host, self.port, backlog=500, start_serving=False)
        self.__server_ssl = await asyncio.start_server(lambda r, w: self.__create_client(r, w, True), self.host, self.ssl, backlog=500, ssl=ssl_context, start_serving=False) if self.ssl is not None else self.__server
        async with self.__server, self.__server_ssl:
            if self.__server_ssl is not self.__server:
                await self.__server_ssl.start_serving()
            await self.__server.serve_forever()

    async def __create_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, ssl=False):
        TIMEOUT = 300
        addr = writer.get_extra_info("peername")
        debug.print("Connection:", *addr)
        alive = True
        while alive:
            alive = False
            try:
                # Get First Line of the Request
                try:
                    request = await asyncio.wait_for(reader.readline(), TIMEOUT)
                except asyncio.TimeoutError:
                    return writer.close()
                # print("Request:", *addr, request)

                try:
                    command, url, version = request.decode().strip().split()
                except ValueError:    return False
                url = urllib.parse.urlparse(url)
                path = url.path or "/"
                query = dict(map(lambda x: urllib.parse.unquote(x).replace("+", " "), q.split("=", 1)) for q in url.query.split("&")) if url.query else {}

                # Parse Headers
                headers = HeaderContainer()
                while (line := (await reader.readline()).decode().strip()):
                    name, values = map(str.strip, line.split(":", 1))
                    headers[name] = Header(name, values)

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
                client = self.client(reader, writer, self.data, headers["host"].value.split(":", 1)[0], *addr, ssl, command, path, query, headers, cookies)
                request = self.request(client, path.split("/")[1:], 0)

                # print("Request Handler")
                while isinstance(request, Request):
                    # print(f"Proc Req: {type(request).__qualname__} {request}")
                    request = await request.handle()
                # print("Request Handled")

                # Compile Client Buffer
                cbuffer = (await client.buffer._compile(client)).strip()

                client.header << Header("Content-Length", len(cbuffer))
                if "Connection" in headers and headers["Connection"].value == "keep-alive":
                    client.header << Header("Connection", "keep-alive")
                    client.header << Header("Keep-Alive", f"timeout={TIMEOUT}", split=", ")
                    alive = True
                buffer = "\r\n".join(filter(None, (
                    f"HTTP/1.1 {client.status.value} {client.status.phrase}",
                    client.header._format(),
                    client.cookie.output(),
                ))).strip() + "\r\n\r\n"

                writer.write(buffer.encode())
                writer.write(cbuffer)
            except Exception as e:
                print(f"Connection: {addr[0]}:{addr[1]}", "".join(traceback.format_exception(e, e, e.__traceback__)))
            finally:
                try:
                    await writer.drain()
                except ConnectionError:    pass
                if not alive:
                    writer.close()