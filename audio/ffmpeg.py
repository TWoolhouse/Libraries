import asyncio
import asyio
from .base import Processor, Properties

async def exc_subproc(cmd: str, data: bytes) -> bytes:
    if not data:
        return b""
    # print(cmd)
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    output = await proc.communicate(data)
    if not proc.returncode:
        return output[0]
    print(output[1].decode("utf8"))
    return b""

class FFmpeg:
    EXE = "D:/Programs/ffmpeg/bin/ffmpeg.exe"

    def __init__(self, cmd: str):
        self.cmd = cmd
        self._active = cmd

    def compile(self, properties: Properties, *args, **kwargs) -> str:
        self._active = self.cmd.format(*args, pipe="pipe:", prop=properties, **kwargs)
        return self._active

    async def call(self, data: bytes, *args, **kwargs) -> bytes:
        return await exc_subproc(self.EXE+" "+self._active.format(*args, **kwargs), data)

class FFmpegProcessor(Processor):
    def __init__(self, cmd: str):
        super().__init__()
        self.ffmpeg = FFmpeg(cmd)

    def open(self, properties: Properties, *args, **kwargs) -> bool:
        """Open the ffmpeg processor before reading / processing can occur"""
        res = super().open(properties)
        self.ffmpeg.compile(self.prop, *args, **kwargs)
        return res

    async def process(self, data: bytes, size: int) -> bytes:
        return await self.ffmpeg.call(data)
