from .controller import Stream, Track, Status
from collections import deque
from interface import Interface

class Single(Stream):

    def __init__(self, track: Track):
        super().__init__()
        self.track = track

    async def open(self):
        await self.track.open()
        self.track.state.status.value = Status.ACTIVE
        await super().open()
    async def close(self):
        await super().close()
        await self.track.close()

    def _bind(self, properties):
        super()._bind(properties)
        self.track._bind(properties)
    def _unbind(self):
        super()._unbind()
        self.track._unbind()

    async def process(self):
        return await self.track.process()

class Queue(Stream):

    _null_track = Track()

    def __init__(self):
        super().__init__()
        self.track = self._null_track
        self.queue = deque()

    async def open(self):
        flag = await self._get_next(Status.INIT)
        await super().open()
        return flag
    # async def close(self):
    #     pass

    async def process(self):
        return await self.track.process()

    async def _get_next(self, cause: Status) -> bool:
        self.track.state.status.value = cause

        if not self.queue:
            self.track = self._null_track
            self.done.set()
            return False

        self.done.clear()

        track: Track = self.queue.popleft()
        track._bind(self.properties)
        self._preload()

        if (await track.state.status.wait(Status.READY)) is not Status.READY:
            return await self._get_next(Status.INVALID)

        track.state.status.value = Status.ACTIVE
        Interface.schedulc(self._wait_next(track))
        self.track = track
        return True

    async def _wait_next(self, track: Track):
        await track.state.status.wait(Status.DONE)
        await self._get_next(Status.DONE)

    def _insert(self, track: Track) -> Track:
        if track.state.status.value is not Status.INIT:
            raise ValueError("Track is not in a state to be added")
        track.state.status.value = Status.QUEUE
        self._preload()

    def _preload(self):
        if self.queue and self.queue[0].state.status.value is Status.QUEUE:
            Interface.schedulc(self._preload_async(self.queue[0]))
    async def _preload_async(self, track: Track):
        try:
            if track.state.status.value is Status.QUEUE:
                track.state.status.value = Status.PREPARE
                await track.open()
            elif track.state.status.value is Status.PREPARE:
                return False
            else:
                track.state.status.value = Status.INVALID
        except Exception as e:
            track.state.status.value = Status.INVALID
            raise
        track.state.status.value = Status.READY
        return True

    def append(self, track: Track) -> Track:
        self.queue.append(track)
        self._insert(track)
        return track
