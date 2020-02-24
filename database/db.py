from database.enums import Type, OP
from database.logic import Table, Column, Condition
import database.sql
import database.logic

import threading
import queue

__all__ = ["Database"]

class Database:
    """A interface to the database file"""

    def __init__(self, filepath: str, new: bool = False):
        self.filepath = filepath
        self.sql = database.sql.Sql(self.filepath+".db")
        if new:
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
        self._thread = threading.Thread(target=self.__loop_database_calls, args=(self._event,))
        self._func_calls = queue.Queue()
        self._data_response = {}

        if new:
            super().open()
            super().new()
            super().close()

    def open(self):
        """Open Database Connection"""
        if not self._event.is_set():
            self._event.set()
            self._thread = threading.Thread(target=self.__loop_database_calls, args=(self._event,))
            self._thread.start()

    def close(self):
        """Close Database File"""
        self._event.clear()

    def __loop_database_calls(self, db_event):
        try:
            super().open()
            try:
                self.load()
            except TypeError:    pass
            while db_event.is_set():
                try:
                    event, func, args, kwargs = self._func_calls.get_nowait()
                except queue.Empty:    continue
                self._data_response[event] = func(*args, **kwargs)
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
        return self.__func_call(super().new)

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