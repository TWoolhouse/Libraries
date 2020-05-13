from interface import Interface
import re
import json

__all__ = ["Buffer", "File", "Python", "wrap"]

def wrap(func):
    def wrapper(*args, **kwargs):
        def inner():
            return func(*args, **kwargs)
        return inner
    return wrapper

class Buffer:

    def __init__(self):
        pass

    async def _compile(self) -> bytes:
        return b"BUFFER"

class File(Buffer):

    def __init__(self, file: str):
        self.file = file

    async def _compile(self) -> bytes:
        async with Interface.open(self.file, "rb") as file:
            return file.read()

class Python(File):

    __re = re.compile("(?:<\\?python)((?:(?!\\?>)(?:\\r?\\n|.))*)(?:\\?>)")

    def __init__(self, file: str, request: "Request"):
        super().__init__(file)
        self.__request = request

    async def _compile(self) -> bytes:
        async with Interface.open(self.file, "r") as file:
            data = file.read()
        return self.__re.sub(self.__match, data).encode()

    def __match(self, match):
        namespace = {
            "request": self.__request,
            "value": self.__wrap,
        }
        return str(eval(match.group(1).strip(), namespace)())

    def __wrap(self, value):
        def wrapper():
            return value
        return wrapper

class Json(Buffer):

    def __init__(self, data):
        self.data = data

    async def _compile(self) -> bytes:
        return json.dumps(self.data).encode()