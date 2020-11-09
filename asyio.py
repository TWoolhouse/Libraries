import asyncio
from interface import Interface
import subprocess
import urllib.request
import http.client
from typing import Union

__all__ = ["Request", "Process", "ProcessFast"]

class Process:

    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL

    def __init__(self, args, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=False, decode=True, **kwargs):
        self.args = args
        self.__started = asyncio.Event()
        # self.__proc
        self.__decode = decode

        async def start():
            nonlocal args
            if shell:
                if isinstance(args, str):
                    args = (args,)
                else:
                    args = (" ".join(map(str, args)),)
                subproc = Interface.loop.subprocess_shell
            else:
                subproc = Interface.loop.subprocess_exec
            factory = lambda: asyncio.subprocess.SubprocessStreamProtocol(asyncio.streams._DEFAULT_LIMIT, Interface.loop)
            transport, protocol = await subproc(factory, *args, stdin=stdin, stdout=stdout, stderr=stderr, **kwargs)
            self.__proc = asyncio.subprocess.Process(transport, protocol, Interface.loop)
            self.__started.set()

        Interface.schedule(start())

    def __await__(self):
        return self.read().__await__()

    @property
    def process(self) -> asyncio.subprocess.Process:
        if not self.__started.is_set():
            raise ValueError("Process has not started")
        return self.__proc

    async def communicate(self, input=None) -> (bytes, bytes):
        await self.__started.wait()
        return await self.__proc.communicate(input)

    async def read(self) -> subprocess.CompletedProcess:
        completed = subprocess.CompletedProcess(self.args, self.__proc.returncode, *await self.communicate())
        if self.__decode:
            completed.stdout = completed.stdout.decode()
            completed.stderr = completed.stderr.decode()
        return completed

class ProcessFast:

    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL

    def __init__(self, args, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=False, decode=True, **kwargs):
        if isinstance(args, subprocess.Popen):
            self.args = args.args
            self.__proc = args
        else:
            self.args = args
            self.__proc = subprocess.Popen(args, stdout=stdout, stderr=stderr, stdin=stdin, shell=shell, **kwargs)
        self.__decode = decode

    def __await__(self):
        return self.read().__await__()

    @property
    def process(self) -> subprocess.Popen:
        return self.__proc

    async def read(self) -> subprocess.CompletedProcess:
        while self.__proc.poll() is None:
            await Interface.next()
        completed = subprocess.CompletedProcess(self.__proc.args, self.__proc.returncode, self.__proc.stdout.read() if self.__proc.stdout else None, self.__proc.stderr.read() if self.__proc.stderr else None)
        if self.__decode:
            completed.stdout = completed.stdout.decode()
            completed.stderr = completed.stderr.decode()
        return completed

class Request:

    def __init__(self, url, **kwargs):
        self.__proc = Interface.process(urllib.request.urlopen, url, **kwargs)

    def __await__(self):
        return self.wait().__await__()

    async def wait(self) -> Union[http.client.HTTPResponse, urllib.request.URLopener]:
        return await self.__proc
