from database.enums import Type, OP
from database.logic import Table, Column, Condition
import database.sql
import database.logic

from interface import Interface
import asyncio
import threading
import queue

__all__ = ["Database", "ThreadDatabase", "AsyncDatabase", "Serialize"]

Serialize = database.sql.Serialize

class Database:
    """A interface to the database file"""

    def __init__(self, filepath: str, new: bool = False):
        self.filepath = filepath
        self.sql = database.sql.Sql(self.filepath+".db")
        if new:
            with self:
                self.new()

    def new(self):
        """Create new/overwrite DB file"""
        self.sql.new_file()
        self.sql.new()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getitem__(self, key: str) -> Table:
        return self.sql.get_table(database.logic.name_table(key))

    def open(self):
        """Open Database Connection"""
        self.sql.open()

    def close(self):
        """Close Database File"""
        self.sql.close()

    def exec(self, stmt: str, params: tuple=None):
        """Execute Raw SQL Statements"""
        return self.sql.exec(stmt, params)

    def table(self, name: str, *columns: Column) -> Table:
        """Create a New Table"""
        return self.sql.table(database.logic.name_table(name), *columns)

    def load(self):
        """Load all Tables in Database"""
        for table in self.sql.select("__metadata__", Condition("id", 0, OP.NE), columns=("id",)):
            id = table[0]
            self.sql.get_tableID(id)
        return self

    @property
    def tables(self) -> tuple:
        """Return Currently Loaded Tables"""
        return tuple(self.sql.tables.keys())

    def insert(self, table: Table, *values, columns: dict={}, id=False):
        """Insert a Row into Table

        columns: dict[Column, str, int] = value
        """
        return self.sql.insert(table.name, *((database.logic.column_name(table, col), value) for col, value in (*zip(table.columns, values), *columns.items())), id=id)

    def select(self, table: Table, *conditions: Condition, columns:tuple=("*",), all=True):
        """Select Columns from Table Where Conditions are Met"""
        conditions = (Condition("id", conditions[0]),) if len(conditions) == 1 and isinstance(
            conditions[0], int) else (database.logic.condition_name(table, c, i) for i, c in enumerate(conditions))
        return self.sql.select(table.name, *conditions, columns=(database.logic.column_name(table, col) for col in columns), all=all)

    def selectID(self, table: Table, *conditions: Condition, all=False):
        """Select ID from Table Where Conditions are Met"""
        conditions = (Condition("id", conditions[0]),) if len(conditions) == 1 and isinstance(
            conditions[0], int) else (database.logic.condition_name(table, c, i) for i, c in enumerate(conditions))
        return self.sql.selectID(table.name, *conditions, all=all)

class ThreadDatabase(Database):

    def __init__(self, filepath: str, new: bool=False):
        super().__init__(filepath, new=False)
        self._event = threading.Event()
        self._state = threading.Event()
        self._thread = threading.Thread(target=self.__loop_database_calls, args=(self._event,))
        self._func_calls = queue.Queue()
        self._data_response = {}

        self._state.set()
        if new:
            self.new()

    def open(self):
        """Open Database Connection"""
        if not self._event.is_set():
            self._event.set()
            self._state.wait()
            self._thread = threading.Thread(target=self.__loop_database_calls, args=(self._event, self._state))
            self._thread.start()
            while self._state.is_set():
                pass

    def close(self):
        """Close Database File"""
        self._event.clear()

    def __loop_database_calls(self, db_event: threading.Event, cl_event: threading.Event):
        try:
            super().open()
            try:
                self.load()
            except TypeError:    pass
            cl_event.clear()
            while db_event.is_set():
                try:
                    event, func, args, kwargs = self._func_calls.get_nowait()
                except queue.Empty:    continue
                try:
                    self._data_response[event] = func(*args, **kwargs)
                except Exception as e:
                    self._data_response[event] = e
                event.set()
                self._func_calls.task_done()
                for e in list(self._data_response.keys()):
                    if not e.is_set():
                        del self._data_response[e]
        except Exception as e:
            try:
                while True:
                    event, f, a, k = self._func_calls.get_nowait()
                    self._data_response[event] = e
                    event.set()
            except queue.Empty: pass
        finally:
            super().close()
            cl_event.set()
            try:
                while True:
                    event, f, a, k = self._func_calls.get_nowait()
                    self._data_response[event] = None
                    event.set()
            except queue.Empty: pass

    def __func_call(self, func, *args, **kwargs):
        event = queue.threading.Event()
        self._func_calls.put((event, func, args, kwargs))
        event.wait()
        res = self._data_response[event]
        if isinstance(res, Exception):
            raise res
        event.clear()
        return res

    def new(self):
        """Create new/overwrite DB file"""
        super().open()
        super().new()
        super().close()

    def exec(self, stmt: str, params: tuple=None):
        """Execute Raw SQL Statements"""
        return self.__func_call(super().exec, stmt, params=params)

    def table(self, name: str, *columns: Column) -> Table:
        """Create a New Table"""
        return self.__func_call(super().table, name, *columns)

    def insert(self, table: Table, *values, columns: dict={}, id=False):
        """Insert a Row into Table

        columns: dict[Column, str, int] = value
        """
        return self.__func_call(super().insert, table, *values, columns=columns, id=id)

    def select(self, table: Table, *conditions: Condition, columns:tuple=("*",), all=True):
        """Select Columns from Table Where Conditions are Met"""
        return self.__func_call(super().select, table, *conditions, columns=columns, all=all)

    def selectID(self, table: Table, *conditions: Condition, all=False):
        """Select ID from Table Where Conditions are Met"""
        return self.__func_call(super().selectID, table, *conditions, all=all)

class AsyncDatabase(Database):

    def __init__(self, filepath: str, new: bool=False):
        super().__init__(filepath)
        self.__event = asyncio.Event()
        self.__event.set()
        self.__queue = asyncio.Queue()
        self.__response = {}
        self.__new = new

    def __await__(self):
        return self.__queue.join().__await__()

    async def __func_call(self, func, *args, **kwargs):
        event = asyncio.Event()
        self.__queue.put_nowait((event, func, args, kwargs))
        await event.wait()
        res = self.__response[event]
        if isinstance(res, Exception):
            raise res
        event.clear()
        return res

    @Interface.submit
    async def serve(self):
        func = await self.__queue.get()
        if func is None:
            self.__shutdown_requests()
            return True

        event, func, args, kwargs = func
        try:
            self.__response[event] = func(*args, **kwargs)
        except Exception as err:
            self.__response[event] = err
        event.set()
        self.__queue.task_done()

        for event in tuple(self.__response.keys()):
            if not event.is_set():
                del self.__response[event]

    @serve.start
    async def __open(self):
        super().open()
        if self.__new:
            self.__new = False
            await self.new()

    @serve.final
    async def __close(self):
        self.__queue.put_nowait(None)
        self.__shutdown_requests()
        super().close()

    def __shutdown_requests(self):
        try:
            while True:
                func = self.__queue.get_nowait()
                if func is None:
                    continue
                event, func, args, kwargs = func
                self.__response[event] = RuntimeError()
        except asyncio.QueueEmpty:    pass

    def open(self):
        raise TypeError(f"Can not Open '{self.__class__.__name__}' directly")

    async def close(self):
        self.serve.cancel()
        await self.serve
        self.__event.set()

    async def new(self):
        return await self.__func_call(super().new)

    async def exec(self, stmt: str, params: tuple=None):
        """Execute Raw SQL Statements"""
        return await self.__func_call(super().exec, stmt, params=params)

    async def table(self, name: str, *columns: Column) -> Table:
        """Create a New Table"""
        return await self.__func_call(super().table, name, *columns)

    async def insert(self, table: Table, *values, columns: dict={}, id=False):
        """Insert a Row into Table

        columns: dict[Column, str, int] = value
        """
        return await self.__func_call(super().insert, table, *values, columns=columns, id=id)

    async def select(self, table: Table, *conditions: Condition, columns:tuple=("*",), all=True):
        """Select Columns from Table Where Conditions are Met"""
        return await self.__func_call(super().select, table, *conditions, columns=columns, all=all)

    async def selectID(self, table: Table, *conditions: Condition, all=False):
        """Select ID from Table Where Conditions are Met"""
        return await self.__func_call(super().selectID, table, *conditions, all=all)
