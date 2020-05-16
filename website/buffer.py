import asyncio
from interface import Interface
import re
import json
from . import error

__all__ = ["Buffer", "File", "Python", "wrap", "wrap"]

def wrap(func):
    def wrapper(*args, **kwargs):
        async def inner():
            c = func(*args, **kwargs)
            if asyncio.iscoroutine(c):
                return await c
            return c
        return inner
    return wrapper

class Buffer:

    def __init__(self):
        pass

    async def compile(self) -> bytes:
        return b"BUFFER"

    def __str__(self) -> str:
        return f"Base Buffer"

class File(Buffer):

    def __init__(self, file: str):
        self.file = file

    async def compile(self) -> bytes:
        try:
            async with Interface.open(self.file, "rb") as file:
                return file.read()
        except FileNotFoundError:
            raise error.BufferRead(self) from None

    def __str__(self) -> str:
        return f"File<{self.file}>"


class Python(File):

    __re = re.compile("(?:<\\?python)((?:(?!\\?>)(?:\\r?\\n|.))*)(?:\\?>)")

    def __init__(self, file: str, request: "Request"):
        super().__init__(file)
        self.__request = request

    async def compile(self) -> bytes:
        try:
            async with Interface.open(self.file, "r", encoding="utf-8") as file:
                data = file.read()
        except FileNotFoundError:
            raise error.BufferRead(self) from None
        namespace = {
            "request": self.__request,
            "value": self.__wrap,
        }
        match = self.__re.search(data)
        while match:
            start, end = match.span()
            new = str(await eval(match[1].strip(), namespace)())
            data = data[:start] + new + data[end:]
            match = self.__re.search(data, start+len(new))
        return data.encode("utf-8")

    def __wrap(self, value):
        async def wrapper():
            return value
        return wrapper

    def __str__(self) -> str:
        return f"Python<File<{self.file}> Request<{self.__request}>>"

class Json(Buffer):

    def __init__(self, data):
        self.data = data

    async def compile(self) -> bytes:
        return json.dumps(self.data).encode()

    def __str__(self) -> str:
        return f"JSON<{self.data}>"