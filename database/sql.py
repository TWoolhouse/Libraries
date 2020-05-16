from database.enums import Type, OP
from database.logic import Table, Column, Condition
import sqlite3
import enum

def type_value(value):
    if isinstance(value, type) and issubclass(value, Serialize):
        return value.__name__
    return enum_val(value)

def enum_val(value, type=enum.Enum) -> str:
    return value.value if isinstance(value, type) else str(value)

def str_types(string: str) -> Type:
    types = []
    while string:
        string = string.strip()
        for t in Type:
            ts = type_value(t)
            pos = string.find(ts)
            if pos != -1:
                types.append(t)
                string = string[:pos]+string[len(ts)+pos:]
    return tuple(types)

class _MetaSerialize(type):
    def __init__(cls, name, bases, attr):
        sqlite3.register_adapter(cls, cls.serial_sql)
        sqlite3.register_converter(name, cls.serial_pyc)
        return super().__init__(name, bases, attr)

class Serialize(metaclass=_MetaSerialize):
    def serial_sql(self) -> bytes:
        raise TypeError("Must SubClass Serialize")
    def serial_pyc(data) -> "Serialize":
        raise TypeError("Must Subclass Serialize")

class Sql:
    """Sql file management"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._file = None
        self.cursor = None
        self.tables = {}

    def table(self, table: str, *columns: Column) -> Table:
        """Create a new Table"""
        self.create_table(table, Column("id", Type.AIPK), *columns)
        tid = self.insert("__metadata__", ("name", table), ("columns", len(columns)), id=True)
        for index, column in enumerate(columns):
            link = ("lid", column.link._id) if column.link else ("lid", 0)
            column._id = self.insert("__columndata__", ("tid", tid), ("loc", index), ("name", column.name), ("type", " ".join(map(type_value, column.types))), link, id=True)
        tbl = Table(table, *columns, id=tid)
        self.tables[tbl.name] = tbl
        return tbl

    def insert(self, table: str, *columns: tuple, id=False) -> int:
        """Insert Row into Table"""
        self.s_insert(table, *zip(*columns))
        if id:
            return self.selectID(table, *map(Condition, *zip(*columns)))

    def selectID(self, table: str, *conditions: Condition, all=False) -> int:
        """Return ID of Row"""
        res = self.select(table, *conditions, columns=("id",), all=all)
        return ((r[0] for r in res) if all else res[0]) if res else False

    def select(self, table: str, *conditions: Condition, columns:tuple=("*",), all=True) -> tuple:
        """Return Columns if Condition is Met"""
        params, cond, prev = [], "", True
        for c in conditions:
            if isinstance(c, Condition):
                params.append(c.value)
                if not prev:
                    cond += " {} ".format(enum_val(OP.AND))
                cond += " {} {} ?".format(c.name, enum_val(c.operator))
                prev = False
            else:
                cond += " {} ".format(enum_val(c))
        res = self.s_select(table, params, cond if cond else None, columns, all=all)
        return res if res else False

    def create_table(self, name: str, *columns: Column):
        cols = ("{} {}".format(col.name, " ".join(map(type_value, col.types))) for col in columns)
        foreign = ("FOREIGN KEY ({}) REFERENCES {}(id)".format(col.name, col.link.name) for col in columns if col.link is not None)
        return self.s_table(name, *cols, *foreign)

    def get_table(self, name: str):
        if name in self.tables:
            return self.tables[name]
        return self._get_table(self.select("__metadata__", Condition("name", name), all=False))
    def get_tableID(self, id: int) -> Table:
        for table in self.tables.values():
            if table._id == id:
                return table
        return self._get_table(self.select("__metadata__", Condition("id", id), all=False))
    def _get_table(self, data) -> Table:
        table = Table(data[1], *self.get_column(data[0]), id=data[0])
        self.tables[data[1]] = table
        return table

    def get_column(self, tid: int, name: str=None) -> Column:
        if name is None:
            return (self._get_column(col) for col in self.select("__columndata__", Condition("tid", tid)))
        return self._get_column(self.select("__columndata__", Condition("tid", tid), Condition("name", name), all=False))
    def get_columnID(self, id: int) -> Column:
        return self._get_column(self.select("__columndata__", Condition("id", id), all=False))
    def _get_column(self, data) -> Column:
        return Column(data[3], *str_types(data[4]), link=self.get_tableID(data[5]) if data[5] else None, id=data[0])

    def exec(self, stmt: str, params=None):
        """Execute a Raw SQL Statement"""
        try:
            if params:
                # print(stmt, params)
                return self.cursor.execute(stmt, params)
            # print(stmt)
            return self.cursor.execute(stmt)
        except (sqlite3.InterfaceError, sqlite3.OperationalError) as err:
            print(stmt, params)
            raise

    def s_table(self, table: str, *columns: str):
        """Underlying SQL Statement for creating a table"""
        return self.exec("CREATE TABLE {} ({})".format(table, ", ".join(columns)))

    def s_insert(self, table: str, columns: tuple, parameters: tuple):
        """Underlying SQL Statement for inserting a row"""
        return self.exec("INSERT INTO {} {} VALUES ({})".format(table, ("("+(", ".join(columns))+")" if columns else ""), ", ".join(("?" for i in range(len(parameters))))), parameters)

    def s_select(self, table: str, parameters: tuple, conditional:str=None, cols:tuple=("*",), all=True) -> tuple:
        """Underlying SQL Statement for selecting rows"""
        self.exec("SELECT {} FROM {}{}".format(", ".join(cols), table, "" if conditional is None else " WHERE {}".format(conditional)), parameters)
        return self.cursor.fetchall() if all else self.cursor.fetchone()

    def new(self):
        """Create a new Database File with Setup"""
        self.create_table("__metadata__", Column("id", Type.AIPK), Column("name", Type.String), Column("columns", Type.Integer))
        self.create_table("__columndata__", Column("id", Type.AIPK), Column.Foreign("tid", Table("__metadata__")), Column("loc", Type.Integer), Column("name", Type.String), Column("type", Type.String), Column.Foreign("lid", Table("__metadata__")))
        self.exec("VACUUM")

    def new_file(self):
        open(self.filepath, "w").close()

    def open(self):
        """Opens file"""
        self._file = sqlite3.connect(self.filepath, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self._file.cursor()
    def close(self):
        """Closes file"""
        self.cursor.close()
        self._file.commit()
        self._file.close()

    def __enter__(self):
        self.open()
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
