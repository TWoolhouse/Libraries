import asyncio

class FFmpeg:

    PATH = "D:/Programs/ffmpeg/bin/ffmpeg.exe"

    def __init__(self, cmd: str, **kwargs: str):
        self.cmd = cmd
        self.kwargs = kwargs
        self._active = ""

    def compile(self, **kwargs):
        self.kwargs |= kwargs
        self._active = f"{self.PATH} {self.cmd.format_map(self.kwargs)}"

    async def call(self, data: bytes) -> bytes:
        if not data:
            return b""
        proc = await asyncio.create_subprocess_shell(
            self._active,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        output = await proc.communicate(data)
        return output[0]
