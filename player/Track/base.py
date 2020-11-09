import asyncio
from .. import util
from ..Status import Status
from interface import Interface
from typing import IO, overload

class TrackBase:

    def __init__(self, *args):
        self._fut: asyncio.Future = None
        self._ready = asyncio.Event()
        self._samplerate = 1
        self._duration = util.ChangeState(-1, "__ge__")
        self._status = util.ChangeState(Status.NONE, "__eq__")
        self._duration_total = 0

    def __await__(self):
        return self.wait().__await__()

    @property
    def status(self) -> Status:
        return self._status.value

    def duration(self, type: ('%', 's', 'f')="f") -> float:
        if type == "%":
            if not self._duration_total:
                raise ValueError("Total Duration Unknown")
            return self._duration.value / self._duration_total
        if type == "s":
            return self._duration.value / self._samplerate
        return self._duration.value

    def duration_total(self, type: ('s', 'f')="f") -> float:
        if type == "s":
            return self._duration_total / self._samplerate
        return self._duration_total

    async def wait(self, duration=None, type: str="%") -> Status:
        if self._status.value >= Status.DONE:
                return self._status.value
        elif isinstance(duration, Status): # Wait for Status
            return await self._status.add(duration)
        elif duration is not None: # Wait for duration
            if not duration:
                pass
            elif type == "%": # Percentage
                await self._ready.wait()
                duration = max(min(duration, 1), -1) * self._duration_total
            elif type == "s": # Seconds
                await self._ready.wait()
                duration *= self._samplerate
            # Frames
            if duration < 0:
                if not self._duration_total:
                    raise ValueError("Total Duration Unknown")
                await self._ready.wait()
                duration += self._duration_total
            return await self._duration.add(int(duration))
        elif self._fut is not None: # Wait til end
            return await self._fut
        return self._status.value

    async def _read(self, size: int) -> list:
        raise NotImplementedError
    def _open(self) -> bool:
        return True
    async def _preload(self, stream: 'sd.RawOutputStream'):
        self._ready.set()
    async def _close(self):
        self._status.clear()
        self._duration.clear()

    def copy(self):
        raise NotImplementedError
