import debug
from typing import Any, Sequence, Tuple, Mapping, Union, overload, Callable, Iterable
from .sql import *
from .sql import fmt_name
import asyncio
import multiprocessing
from interface import Interface

__all__ = ["Database", "DatabaseAsync"]

class DBInterface:

    def __init__(self, name: str, db: "Database", cursor: Cursor):
        self._db = db
        self.__name = name
        self.__c = cursor

    def __getitem__(self, name: str) -> Table:
        return self._db[name]

    def exec(self, stmt: str, params: Sequence[Any]=()):
        """Execute Raw SQL Statement"""
        return self.__c.exec(stmt, params)
        # raise RuntimeError("Function Should have been Overriden")
    def insert(self, tbl: Table, *vals: Tuple[Any, ...], cols: Mapping[Union[Column, str, int], Any]={}) -> int:
        return self.__c.insert(tbl, *vals, cols=cols)
    def fetch(self, amount: int=1) -> Iterable[Row]:
        """Fetch Rows From Last Selection
        Amount: 0 is All"""
        return self.__c.fetch(amount)

    @overload
    def select(self, tbl: Table, *conditions: Tuple[Condition, ...], cols: Sequence[Union[Column, str, int]]=()) -> Callable[[int], Iterable[Row]]:
        ...
    @overload
    def select(self, tbl: Join, *conditions: Tuple[Condition, ...], cols: Sequence[Column]=()) -> Callable[[int], Iterable[Row]]:
        ...
    def select(self, tbl, *conditions, cols=()) -> Callable[[int], Iterable[Row]]:
        """Select"""
        return self.__c.select(tbl, *conditions, columns=cols)

    def finish(self):
        self._db._close_dbi(self.__name)

    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.finish()

class Database:

    _get_interface = DBInterface

    def __init__(self, filename: str):
        self.filename = filename
        self.__connection = None
        self.__cursors = {}
        self.__tables = {}

    def connection(self) -> bool:
        return bool(self.__connection)

    def open(self) -> bool:
        if not self.connection():
            debug.print(f"Open {self.__class__.__name__} in {self.filename}")
            self.__connection = connection(self.filename)
            self.__cursors["default"] = None
            for k,c in self.__cursors.items():
                self.__cursors[k] = self.__interface(k)
            self.__tables = self.__connection.cursor().load({})
            return True
        return False

    def close(self) -> bool:
        if self.__connection:
            debug.print(f"Close {self.__class__.__name__} in {self.filename}")
            self.__connection.close()
            return True
        return False

    def _close_dbi(self, dbi_name: str):
        self.__cursors.pop(dbi_name)
        self.__connection.close_cursor(dbi_name)

    def __call__(self, name: str="default") -> DBInterface:
        try:
            return self.__cursors[name]
        except KeyError:
            c = self.__cursors[name] = self.__interface(name)
            return c

    def __interface(self, name: str) -> DBInterface:
        return self._get_interface(name, self, self.__connection.cursor(name))

    interface = __call__

    def __getitem__(self, name: Union[str, int]) -> Table:
        if isinstance(name, int):
            return self.__tables[name]
        return self.__tables[fmt_name(name)]

    def __enter__(self):
        debug.print("Opening")
        self.open()
        return self
    def __exit__(self, *args):
        debug.print("Closing")
        self.close()

    #---DB Calls Only Accessable through default Cursor---#
    def new(self):
        if not self.connection():
            open(self.filename, "w").close()
        else:
            raise ValueError("Connection Must not be Closed")

    def table(self, name: str, *columns: Tuple[Column, ...]) -> Table:
        try:
            return self[name]
        except KeyError:
            return self.__connection.cursor().create_table(self.__tables, name, *columns)

class DBInterfaceAsync(DBInterface):

    # def __init__(self, *args):
    #     super().__init__(*args)

    @debug.catch
    async def __func_call(self, func, *args, **kwargs):
        event = asyncio.Event()
        self._db._queue.put_nowait((event, func, args, kwargs))
        await event.wait()
        response = self._db._queue_response[event]
        if isinstance(response, Exception):
            raise response
        event.clear()
        return response
        # self._db._queue.task_done()

    async def exec(self, stmt: str, params: Sequence[Any]=()):
        """Execute Raw SQL Statement"""
        return await self.__func_call(super().exec, stmt, params)
    async def insert(self, tbl: Table, *values: Tuple[Any, ...], cols: Mapping[Union[Column, str, int], Any]={}) -> int:
        return await self.__func_call(super().insert, tbl, *values, cols=cols)

    @overload
    async def select(self, tbl: Table, *conditions: Tuple[Condition, ...], cols: Sequence[Union[Column, str, int]]=()) -> Callable[[int], Iterable[Row]]:
        ...
    @overload
    async def select(self, tbl: Join, *conditions: Tuple[Condition, ...], cols: Sequence[Column]=()) -> Callable[[int], Iterable[Row]]:
        ...
    async def select(self, tbl, *conditions, cols=()) -> Callable[[int], Iterable[Row]]:
        """Select"""
        return await self.__func_call(super().select, tbl, *conditions, cols=cols)

class DatabaseAsync(Database):

    _get_interface = DBInterfaceAsync

    def __init__(self, filename: str):
        super().__init__(filename)
        self._queue = asyncio.Queue()
        self._queue_response = {}
        self.__active = False

    def connection(self) -> bool:
        return self.__active and super().connection()

    @debug.catch
    async def __func_call(self, func, *args, **kwargs):
        event = asyncio.Event()
        self._queue.put_nowait((event, func, args, kwargs))
        await event.wait()
        response = self._queue_response[event]
        if isinstance(response, Exception):
            raise response
        event.clear()
        return response
        # self._queue.task_done()

    @Interface.Repeat
    async def __serve(self):
        event, func, args, kwargs = await self._queue.get()
        try:
            self._queue_response[event] = func(*args, **kwargs)
        except Exception as err:
            self._queue_response[event] = err
        event.set()
        self._queue.task_done()

        for event in tuple(self._queue_response.keys()):
            if not event.is_set():
                del self._queue_response[event]

    @__serve.enter
    def __enter(self):
        pass

    @__serve.exit
    def __exit(self):
        self.__serve_loop.cancel()
        self.__active = False
        self.__shutdown()
        super().close()

    def __shutdown(self):
        try:
            while True:
                func = self._queue.get_nowait()
                self._queue.task_done()
                if func is None:
                    continue
                event, func, args, kwargs = func
                self._queue_response[event] = RuntimeError()
        except asyncio.QueueEmpty:    pass

    async def __aenter__(self):
        return self.__enter__()
    async def __aexit__(self, *args):
        return self.__exit__(*args)

    def open(self) -> bool:
        self.__active = True
        if super().open():
            self.__serve_loop = self.__serve(self)
            return True
        return False

    def close(self) -> bool:
        self._queue.put_nowait([asyncio.Event(), None, None, None])
        return True

    async def table(self, name: str, *cols: Column) -> Table:
        return await self.__func_call(super().table, name, *cols)
