import asyncio
from interface import Interface
import re
import json
from . import error
from path import PATH
from caching import cache

import debug

__all__ = ["Buffer", "File", "Python", "wrap", "clear"]

def wrap(func):
    def wrapper(*args, **kwargs):
        async def inner():
            c = func(*args, **kwargs)
            if asyncio.iscoroutine(c):
                return await c
            return c
        return inner
    return wrapper

# def clear():
#     File.open.

class Buffer:

    cache_disable = False

    def __init__(self, cache_disable: bool=None):
        if cache_disable is not None:
            self.cache_disable = cache_disable

    async def open(self) -> bytes:
        raise error.BufferRead(self)
    async def data(self) -> bytes:
        return await self.open()

    async def compile(self) -> bytes:
        return await self.open()

    def __str__(self) -> str:
        return f"Base Buffer"

class File(Buffer):

    def __init__(self, file: str, cache_disable: bool=None):
        super().__init__(cache_disable)
        self.file = file

    @staticmethod
    @cache
    async def open(filename) -> bytes:
        try:
            async with Interface.AIOFile(filename, "rb") as file:
                return file.read()
        except FileNotFoundError:
            raise error.BufferRead(filename) from None

    async def compile(self) -> bytes:
        return await self.open(self.file, override=self.cache_disable)

    def __str__(self) -> str:
        return f"File<{self.file}>"

class Python(File):

    _Request, _Client = None, None

    __re = re.compile(r"(?:<py>)((?:(?!</py>)(?:\r?\n|.))*)(?:</py>)")

    def __init__(self, file: str, request: "Request"=None, cache_disable: bool=None):
        super().__init__(file, cache_disable)
        self.__request = request

    def __await__(self):
        return self.compile().__await__()

    @staticmethod
    @cache
    async def open(filename) -> bytes:
        try:
            async with Interface.AIOFile(filename, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            raise error.BufferRead(filename) from None

    @debug.catch
    async def compile(self, request: ('Request', 'Client')=None) -> bytes:
        data = await self.open(self.file, override=self.cache_disable)
        namespace = {
            "path": PATH,
            "request": self.__request,
            "value": self.__wrap,
            "buffer": self.__insert_buffer,
        }
        if isinstance(request, self._Request):
            namespace["client"] = request.client
            namespace["request"] = request
        elif isinstance(request, self._Client):
            namespace["client"] = request
        match = self.__re.search(data)

        output = b""
        while match:
            try:
                new = await eval(match[1].strip(), namespace)()
            except Exception:
                print(match[1].strip())
                raise
            if not isinstance(new, bytes):
                new = str(new).encode("utf8")
            start, end = match.span()
            output += data[:start].encode("utf8") + new
            data = data[end:]
            match = self.__re.search(data)
        return output + data.encode("utf8")

    def __wrap(self, value):
        async def wrapper():
            if asyncio.iscoroutine(value):
                return await value
            return value
        return wrapper
    def __insert_buffer(self, path, type="py"): # Implement Types
        return Python(path, self.__request).compile

    def __str__(self) -> str:
        return f"Python<File<{self.file}> Request<{self.__request}>>"

class Json(Buffer):

    def __init__(self, data):
        super().__init__()
        self.data = data

    async def compile(self) -> bytes:
        return json.dumps(self.data).encode()

    def __str__(self) -> str:
        return f"JSON<{self.data}>"
