import debug
import sqlite3
from . import error as dberror
import enum
from .op import Type, OP, Join
_Join = Join
from typing import Any, Union, Sequence, Tuple

__all__ = ["Table", "Column", "Condition", "Join", "Serialize", "Cursor", "Connection", "connection", "Row"]

def get_enum_value(value, type=enum.Enum) -> str:
    if isinstance(value, type):
        return value.value
    return value

def get_etype_value(value) -> str:
    if isinstance(value, type) and issubclass(value, Serialize):
        return value.__name__
    return get_enum_value(value, Type)

def fmt_name(name: str) -> str:
    return str(name).strip().replace(" ", "").lower()

def encol(table: "Table", column) -> "Column":
    if isinstance(column, Column):
        return column
    return table[column]

def enstrc(table: "Table", column) -> str:
    if isinstance(column, str):
        return column
    if isinstance(column, int):
        return table[column].name
    return column.name

def enstr(column) -> str:
    if isinstance(column, Column):
        return column.name
    return column

class Row(sqlite3.Row):

    def __repr__(self) -> str:
        return f"({', '.join(map(str, self))})"

    def items(self):
        yield from zip(self.keys(), self)

class Table:
    def __init__(self, name: str, *columns: Tuple['Column', ...], id: int=0):
        self.id = id
        self.name = fmt_name(name)
        self.columns = [Column("id", Type.AIPK), *columns]
        for col in self.columns:
            col.parent = self
        self.__named_columns = {col.name: col for col in self.columns}

    def __getitem__(self, key: Union[str, int]) -> "Column":
        if isinstance(key, str):
            return self.__named_columns[key]
        return self.columns.__getitem__(key)
        raise KeyError(key)
    get = __getitem__
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.id}.{len(self.columns)}:{self.name} {self.columns}>"

class Column:

    def __init__(self, name: str, *types: Tuple[Type, ...], link: "Column"=None, id: int=0):
        self.id = id
        self.name = fmt_name(name)
        self.types = types
        self.link = link
        self.parent = None

    @classmethod
    def Foreign(cls, name: str, link: "Column", delete="CASCADE", update="CASCADE", *types: Tuple[Type, ...]) -> "Column":
        if isinstance(link, Table):
            link = link[0]
        col = cls(name, Type.INT, *types, link=link)
        col._on = (delete, update)
        return col

    def __repr__(self) -> str:
        return f"{self.__class__.__name__ if not self.link else self.__class__.__name__+'.Foreign'}<{self.parent.id if self.parent else 0}.{self.id}:{self.name} ({' '.join(map(get_etype_value, self.types))})>"

class Condition:
    def __init__(self, value, column: Union[Column, str, int]=None, op: OP=OP.EQ):
        self.value = value
        self.column = column
        self.op = op

    def __repr__(self) -> str:
        return f"Condition<{self.column} {self.op} {self.value}>"

class Join:

    Type = _Join

    def __init__(self, first: Union[Column, Table], second: Column, jtype: Join=Join.INNER):
        self.first = first if isinstance(first, Column) else first[0]
        self.second = second if isinstance(second, Column) else second[0]
        self.jtype = jtype

    def __getitem__(self, key: str):
        raise TypeError("Must use Column when using Join")

class _MetaSerialize(type):
    def __init__(cls, name, bases, attr):
        sqlite3.register_adapter(cls, cls.serial_sql)
        sqlite3.register_converter(name, cls.serial_pyc)
        return super().__init__(name, bases, attr)

class Serialize(metaclass=_MetaSerialize):
    def serial_sql(self) -> bytes:
        raise dberror.Serialize(self, "Must SubClass 'Serialize'")
    def serial_pyc(cls, data: bytes) -> "Serialize":
        raise dberror.Serialize(cls, "Must SubClass 'Serialize'")

class Cursor:

    def __init__(self, cursor: sqlite3.Cursor):
        self.__cursor = cursor

    def __repr__(self) -> str:
        return f"Cursor<{self.__cursor.connection.__repr__(self)}>"

    @debug.log
    def fetch(self, amount: int=1) -> [Row,]:
        """Fetch Rows From Last Selection
        Amount: 0 is All"""
        if not amount:
            return self.__cursor.fetchall()
        if amount == 1:
            return self.__cursor.fetchone()
        else:
            return self.__cursor.fetchmany(amount)

    def select(self, table: Table, *conditions: Tuple[Condition, ...], columns: Column=()) -> fetch:
        if isinstance(table, Join):
            name = f"{table.first.parent.name} {table.jtype.value} JOIN {table.second.parent.name} ON {table.first.parent.name}.{table.first.name}={table.second.parent.name}.{table.second.name}"
            params, condition = self.__select_join(table, conditions)
            columns = map(lambda x: f"{x.parent.name}.{x.name}", columns)
        else:
            name = table.name
            params, condition = self.__select_std(table, conditions)
            columns = map(lambda x: enstrc(table, x), columns)
        self._s_select(name, params, columns, condition)
        return self.fetch

    def __select_join(self, table: Table, conditions: (Condition,)) -> (list, str):
        params = []
        condition = ""
        prev_op = False
        for c in conditions:
            if isinstance(c, OP):
                prev_op = False
                condition += f" {get_enum_value(c)} "
            else:
                if prev_op:
                    condition += f" {get_enum_value(OP.AND)} "
                condition += f"{c.column.parent.name}.{c.column.name} {get_enum_value(c.op)} ?"
                params.append(c.value)
                prev_op = True
        return params, condition

    def __select_std(self, table: Table, conditions: (Condition,)) -> (list, str):
        if conditions and isinstance(conditions[0], int):
            return (conditions[0],), "id IS ?"
        params = []
        condition = ""
        prev_op = False
        for i, c in enumerate(conditions, start=1):
            if isinstance(c, OP):
                prev_op = False
                condition += f" {get_enum_value(c)} "
            else:
                if prev_op:
                    condition += f" {get_enum_value(OP.AND)} "
                if c.column is None:
                    c.column = i
                condition += f"{enstrc(table, c.column)} {get_enum_value(c.op)} ?"
                params.append(c.value)
                prev_op = True
        return params, condition

    def insert(self, table: Table, *values: Any, cols: dict={}) -> int:
        return self._s_insert_into(table.name, *zip(*((enstrc(table, col), val) for col, val in (*zip(table.columns[1:], values), *cols.items()))))

    def create_table(self, tables: dict, name: str, *columns: Column) -> Table:
        fname = fmt_name(name)
        ct = (f"{col.name} {' '.join(map(get_etype_value, col.types))}" for col in columns)
        _on_modes = {"NULL": "SET NULL", "DEFAULT": "SET DEFAULT", "RESTRICT": "RESTRICT", "ACTION": "NO ACTION", "CASCADE": "CASCADE"}
        fc = (f"FOREIGN KEY ({col.name}) REFERENCES {col.link.parent.name}({col.link.name}) {f'ON DELETE {_on_modes.get(col._on[0].upper(), col._on[0])}' if hasattr(col, '_on') and col._on[0] else ''} {f'ON UPDATE {_on_modes.get(col._on[1].upper(), col._on[1])}' if hasattr(col, '_on') and col._on[1] else ''}".strip() for col in columns if col.link is not None)
        self._s_create_table(fname, f"id {Type.AIPK.value}", *ct, *fc)
        tid = self._s_insert_into("__metadata__", ("name",), (fname,))
        for index, col in enumerate(columns, start=1):
            col.id = self._s_insert_into("__columndata__", ("tid", "idx", "name", "type", "lid"), (tid, index, col.name, ",".join(map(get_etype_value, col.types)), col.link.id+1 if col.link else None))
        # tbl = Table(name, *columns, id=tid)
        return self.__load_table(tables, tid, fname)

    @debug.call
    def create_new(self):
        self.exec("PRAGMA foreign_keys=true")
        self.exec("PRAGMA auto_vacuum=FULL")
        self._s_create_table("__metadata__", f"id {Type.AIPK.value}", f"name {Type.STR.value}")
        self._s_create_table("__columndata__", f"id {Type.AIPK.value}", f"tid {Type.INT.value}", f"idx {Type.INT.value}", f"name {Type.STR.value}", f"type {Type.STR.value}", f"lid {Type.INT.value}", f"FOREIGN KEY (tid) REFERENCES __metadata__(id) ON DELETE CASCADE ON UPDATE CASCADE", f"FOREIGN KEY (lid) REFERENCES __columndata__(id) ON DELETE CASCADE ON UPDATE CASCADE")

    @debug.log
    @debug.catch
    def exec(self, stmt: str, params: tuple=()):
        """Execute Raw SQL Statement"""
        self.__cursor.execute(stmt, params)
        return self

    def _s_select(self, table: str, params: tuple, columns: (str,)=("*",), condition: str=None):
        self.exec(f"SELECT {c if (c := ', '.join(columns)) else '*'} FROM {table} {f'WHERE {condition}' if condition else ''}", params)

    def _s_insert_into(self, table: str, columns: (str,), values: tuple) -> int:
        self.exec(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({('?,'*len(values))[:-1]})", values)
        return self.__cursor.lastrowid

    def _s_create_table(self, name: str, *columns: str):
        self.exec(f"CREATE TABLE IF NOT EXISTS {name} ({', '.join(columns)})")

    def close(self):
        try:
            self.__cursor.close()
        except sqlite3.ProgrammingError:
            pass

    def load(self, tables: dict) -> dict:
        try:
            self._s_select("__metadata__", ())
        except sqlite3.OperationalError:
            self.create_new()
            return tables
        for tbl in self.fetch(0):
            self.__load_table(tables, *tbl)
        return tables

    def __load_table(self, tables: dict, tid: int, name: str) -> Table:
        if name in tables:
            return tables[name]
        tbl = tables[name] = {0: Column(tid)}
        self._s_select("__columndata__", (tid,), condition="tid IS ?")
        for col in self.fetch(0):
            self.__load_column(tables, col)
        cols = [tbl[i] for i in sorted(tbl.keys())][1:]
        tbl = tables[tid] = tables[name] = Table(name, *cols, id=tid)
        return tbl

    def __load_column(self, tables: dict, col: (int, dict)) -> Column:
        if isinstance(col, int):
            self._s_select("__columndata__", (col,), condition="id IS ?")
            return self.__load_column(tables, self.fetch())
        for c in (clm for tbl in tables.values() for clm in (tbl.values() if isinstance(tbl, dict) else tbl.columns)):
            if c.id == col["id"]:
                return c
        table = str(col["tid"])
        for tbl in tables.values():
            if tbl[0].name == table:
                table = tbl
                break

        column = table[col["idx"]] = Column(col["name"], *col["type"].split(","), link=self.__load_column(tables, col["lid"]) if col["lid"] else None, id=col["id"])
        return column

class Connection(sqlite3.Connection):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = args[0]
        self.row_factory = Row
        self.__cursors = {}
        self.cursor()
        self.__open = True
        self.cursor().exec("PRAGMA threads=4")

    def cursor(self, name: str="default") -> Cursor:
        try:
            return self.__cursors[name]
        except KeyError:
            c = self.__cursors[name] = Cursor(super().cursor())
            return c

    def close(self):
        self.__open = False
        self.cursor().exec("PRAGMA optimize")
        for cursor in self.__cursors.values():
            cursor.close()
        self.commit()
        super().close()

    def close_cursor(self, name: str):
        self.__cursors.pop(name).close()

    def new(self):
        self.cursor().create_new()

    def __bool__(self) -> bool:
        return self.__open

    def __repr__(self, cursor=None) -> str:
        if cursor:
            for k,c in self.__cursors.items():
                if c is cursor:
                    return k
            return None
        return super().__repr__()

def connection(filename: str) -> Connection:
    return sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=debug.flag, factory=Connection)
