import urllib.request
import http.client
from interface import Interface
from typing import Union
import subprocess

class Process(subprocess.Popen):

    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL

    def __init__(self, args, stdout=None, stderr=None, stdin=None, shell=False,  **kwargs):
        super().__init__(args, stdout=stdout, stderr=stderr, stdin=stdin, shell=shell, **kwargs)

    def __await__(self):
        return self.read().__await__()

    async def read(self) -> subprocess.CompletedProcess:
        while self.poll() is None:
            await Interface.next()
        return subprocess.CompletedProcess(self.args, self.returncode, self.stdout.read() if self.stdout else None, self.stderr.read() if self.stderr else None)

class Request:
    def __init__(self, url, **kwargs):
        self.__proc = Interface.process(urllib.request.urlopen, url, **kwargs)

    def __await__(self):
        return self.wait().__await__()

    async def wait(self) -> Union[http.client.HTTPResponse, urllib.request.URLopener]:
        return await self.__proc



count = 0
# initialise = Batch()
# terminate = Batch()

class stest:
    def __init__(self, x: int):
        self.x = x

    @Interface.Repeat
    def run(self, y: int):
        self.x += 1
        print(self.x)
        if self.x >= y:
            return True

    @run.enter
    def start(self, y):
        print("Start", self, y)
    @run.exit
    def end(self, y):
        print("End", self, y)

def lol():
    print("LOL")
    return "lol"

def xd(x: int):
    print(f"XD {x}")
    if x > 0:
        Interface.terminate.schedule(xd, x-1)

async def main():
    y = Interface.terminate.schedule(xd, 3)
    x = Interface.schedule(lol)
    print(await x)

    t = stest(0)
    x = t.run(t, 3)
    async with Interface.AIOFile("test.py") as file:
        print(file.name)
        print(file.read())

    Interface.stop()

if __name__ == "__main__":
    Interface.schedule(main())
    Interface.main()