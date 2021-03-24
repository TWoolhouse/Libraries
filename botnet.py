import node
import enum
import asyio
import asyncio
import functools
import collections
from typing import Any
from interface import Interface

__all__ = ["Botnet", "ControlCentre"]

class Permisson(enum.IntEnum):
    NONE = 0
    WORKER = 1
    MAX = 255

class Botnet:

    class Client(node.Client):
        bot: 'Botnet'

        async def open(self):
            if await super().open():
                await self.setup_config()
                return True
            return False

        async def setup_config(self):
            CMD = "setup_config"
            self.send({
                "job_count": 0,
            }, CMD)

            config: dict = (await self.recv(CMD))[0].data
            self.bot.authority = Permisson(config["auth"])

        async def dsptch_process(self, data: node.Data):
            jid, iid = data.tag
            data.data, done = await self.bot.programs[int(jid)].process(data.data)
            if not done:
                data.tag.append(node.Tag(False))
            self.send(data)

        async def dsptch_job_load(self, data: node.Data):
            PREFIX = "job_load_"
            jid: int = data.data
            tag = node.Tag(jid)
            prog = (await self.recv(f"{PREFIX}program", tag))[0].data
            self.bot.programs[jid] = prog
            prog.bot = self.bot
            self.send(True, f"{PREFIX}done", tag)

        async def dsptch_job_unload(self, data: node.Data):
            CMD = "job_unload"
            jid = data.data
            del self.bot.programs[jid]
            self.send(True, CMD, node.Tag(jid))

        async def create_job(self, program: 'Program', files, save=False) -> int:
            """Creates job on server from a Program spec. Returns Job ID"""
            PREFIX = "create_job_"
            self.send(program, PREFIX[:-1])
            jid: int = (await self.recv(f"{PREFIX}id"))[0].data
            jtag = node.Tag(jid)
            self.send({
                "file_count": len(files),
                "save": save,
            }, f"{PREFIX}meta", jtag)
            for file in files:
                self.send(file, f"{PREFIX}file", jtag)
            await self.recv(f"{PREFIX}done", jtag)
            return jid
            # TODO Files & Fail

        async def finish_job(self, job: int) -> list[Any]:
            PREFIX = "finish_job_"
            self.send(job, PREFIX[:-1])
            tag = node.Tag(job)
            count = (await self.recv(f"{PREFIX}count", tag))[0].data
            data = await self.recv(f"{PREFIX}item", tag, wait=count)
            return (i.data for i in data)

    def __init__(self, addr: str, port: int):
        self.connection = self.Client(addr, port)
        self.connection.bot = self
        self.authority = Permisson.NONE
        self.programs: dict[int, Program] = {}

    def __enter__(self):
        raise NotImplementedError
        return self
    async def __aenter__(self):
        await self.connection.__aenter__()
        return self
    async def __aexit__(self, *args):
        await self.connection.__aexit__(*args)

    async def create_job(self, program: 'Program', files, save=False) -> int:
        return await self.connection.create_job(program, files, save=save)

    async def feed(self, job: int, *data):
        """Send data items for a Job ID"""
        for item in data:
            self.connection.send(item, "FEED", node.Tag(job))

    async def wait(self, job: int):
        return await self.connection.finish_job(job)

class ControlCentre:

    class SClient(node.SClient):
        """Server Side Client"""
        @property
        def cnc(self) -> 'ControlCentre':
            return self.server.cnc
        worker: 'ControlCentre.Worker'

        async def open(self):
            await super().open()
            await self.setup_config()
            Interface.schedulc(self.cnc.worker_run(self.worker))
        async def close(self):
            addr = self.server.connections[self]
            await super().close()
            # print(addr)

        async def setup_config(self) -> dict:
            CMD = "setup_config"
            config: dict = (await asyncio.wait_for(self.recv(CMD), 15))[0].data
            self.send({
                "auth": Permisson.WORKER.value,
            }, CMD)

            await self.cnc.add_worker(self, **config)

        async def dsptch_kill(self, data: node.Data):
            """Kill the Control Server"""
            # TODO: Req Permisson
            await self.cnc.kill()
            return True
        async def dsptch_cmd(self, data: node.Data):
            """Sends Data Command to all other Connections"""
            print("CMD Input:", type(data.data), data)
            await Interface.gather(*(con.send(data) for con in (c for c in self.server.connections if c is not self)))
        async def dsptch_feed(self, data: node.Data):
            """Distribute Feed Data across network"""
            self.cnc.feed(int(data.tag[0]), data.data)
            return True
        async def dsptch_create_job(self, data: node.Data):
            """Create Job to Distribute Program to Network ready for Data Feed"""
            PREFIX = "create_job_"
            jid = self.cnc.unique()
            jtag = node.Tag(jid)
            self.send(jid, f"{PREFIX}id")
            meta_data: dict = (await self.recv(f"{PREFIX}meta", jtag))[0].data
            files = await self.recv(f"{PREFIX}file", jtag, wait=meta_data["file_count"])
            await self.cnc.create_job(jid, data.data, files, save=meta_data.get("save", False))
            await self.send(True, f"{PREFIX}done", jtag)
            return True
            # TODO: Files
        async def dsptch_finish_job(self, data: node.Data):
            """Finish Job"""
            PREFIX = "finish_job_"
            job = await self.cnc.finish_job(data.data)
            tag = node.Tag(job.id)
            self.send(job.count, f"{PREFIX}count", tag)
            CMD = f"{PREFIX}item"
            for i in range(job.count):
                item: ControlCentre.Item = await job.done.get()
                self.send(item.data, CMD, tag, node.Tag(item.id))
            return True

        async def process(self, data, job: int, item: int) -> tuple[Any, bool]:
            CMD = "process"
            tags = node.Tag(job), node.Tag(item)
            self.send(data, CMD, *tags)
            result = (await self.recv(CMD, *tags))[0]
            return (result.data, (False not in result.tag))

        async def job_load(self, job: 'ControlCentre.Job') -> bool:
            PREFIX = "job_load_"
            tag = node.Tag(job.id)
            self.send(job.id, PREFIX[:-1])
            self.send(job.program, f"{PREFIX}program", tag)
            return (await self.recv(f"{PREFIX}done", tag))[0].data

        async def job_unload(self, job: 'ControlCentre.Job') -> bool:
            CMD = "job_unload"
            self.send(job.id, CMD)
            return (await self.recv(CMD, node.Tag(job.id)))[0].data

    class Worker:
        ACTIVE = 3
        def __init__(self, connection: 'ControlCentre.SClient', job_max: int):
            self.connection = connection
            self.queue: list[ControlCentre.Item] = collections.deque()
            self.semaphore = asyncio.BoundedSemaphore(self.ACTIVE)
            self.jobs: set[ControlCentre.Job] = set()
            self.jobs_max: int = job_max

        async def process(self, item: 'ControlCentre.Item'):
            # TODO: Send to client and await for result
            res, done = await self.connection.process(item.data, item.job.id, item.id)
            return res
            # TODO: On fail

        async def job_load(self, job: 'ControlCentre.Job') -> bool:
            # TODO: Send info for Job
            if job in self.jobs or (self.jobs_max and len(self.jobs) >= self.jobs_max):
                return None
            try:
                self.jobs_max -= 1
                done = await self.connection.job_load(job)
            finally:
                self.jobs_max += 1

            if done:
                self.jobs.add(job)
                return True
            return False

        async def job_unload(self, job: 'ControlCentre.Job'):
            # TODO: Tell Client to forget Job
            if job not in self.jobs:
                return None
            return await self.connection.job_unload(job)

    class Job:
        def __init__(self, id, program):
            self.id: int = id
            self.program: Program = program
            self.active: int = 0
            self.count: int = 0

            self.done = asyncio.Queue()

    class Item:
        def __init__(self, job: 'ControlCentre.Job', data):
            self.id: int = job.count
            self.job: ControlCentre.Job = job
            self.data = data

            self.job.count += 1
            self.job.active += 1

    @staticmethod
    def Authorise(level: Permisson):
        def auth_decorator(func):
            @functools.wraps(func)
            def auth_wrapper(bot: Botnet, *args, **kwargs):
                if bot.authority < level:
                    raise ValueError(f"{level} required: {bot.authority}")
                return func(bot, *args, **kwargs)
            return auth_wrapper
        return auth_decorator

    def __init__(self, port: int):
        self.server = node.Server("", port, client=self.SClient, echo=node.dispatch.echo)
        self.server.cnc = self
        self.jobs: dict[int, ControlCentre.Job] = {}
        self._unique_ids = set()
        self.manager = asyio.MultiQueue()

    async def create_job(self, jid: int, program: 'Program', files: list, save=False):
        job = self.jobs[jid] = self.Job(jid, program)
        self.manager.create(job, asyncio.Queue())
        Interface.schedulc(self.update_worker_jobs())
        return jid

    async def finish_job(self, jid: int) -> 'ControlCentre.Job':
        job: ControlCentre.Job = self.jobs[jid]
        que = self.manager[job]
        await que.join()
        self.manager.delete(job)
        Interface.schedulc(self.update_worker_jobs(job))
        # if not save:
        del self.jobs[jid]
        self.unique(jid)
        return job

    def feed(self, jid: int, data):
        job: ControlCentre.Job = self.jobs[jid]
        self.manager[job].put_nowait(self.Item(
            job, data
        ))

    async def update_worker_jobs(self, remove: Job=None):
        if remove is not None:
            await Interface.gather(*(client.worker.job_unload(remove) for client in self.server.connections.keys()))
        await Interface.gather(*(client.worker.job_load(job) for client in self.server.connections.keys() for job in self.jobs.values()))

    async def add_worker(self, connection: SClient, job_count: int=0, **kw) -> Worker:
        worker =  self.Worker(connection, job_count)
        connection.worker = worker
        await Interface.gather(*(worker.job_load(job) for job in self.jobs.values()))
        return worker

    async def worker_run(self, worker: Worker):
        while True:
            async with worker.semaphore:
                try:
                    item: ControlCentre.Item = await self.manager.get(*worker.jobs)
                except KeyError as e:
                    await Interface.next()
                    continue
                try:
                    item.data = data = await worker.process(item)
                    item.job.done.put_nowait(item)
                except ConnectionError as e:
                    print(e)
                    raise
                    # Connection Closed
                    # Append unfinished items
                    return

    def unique(self, uid=None) -> int:
        if uid is not None:
            self._unique_ids.discard(uid)
            return
        for i in range(2**16):
            if i not in self._unique_ids:
                self._unique_ids.add(i)
                return i
        raise ValueError("Max Unique ID's Reached")

    async def kill(self):
        self.server.close()

    def __enter__(self):
        raise NotImplementedError
        return self
    async def __aenter__(self):
        flag = bool(self.server)
        await self.server.__aenter__()
        if not flag:
            pass
        return self
    async def __aexit__(self, *args):
        await self.server.__aexit__(*args)

    async def serve(self) -> bool:
        await self.__aenter__()

class Program:

    def __init__(self):
        self.bot: Botnet

    async def process(self, data: Any):
        pass
