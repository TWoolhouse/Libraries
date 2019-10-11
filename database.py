import _database
from _database.enums import Type, OP
from _database.logic import Table, Column, Condition

class Database:
    """A interface to the database file"""

    def __init__(self, filepath: str, new: bool = False):
        self.filepath = filepath
        self.sql = _database.sql.Sql(self.filepath+".db")

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
        return self.sql.get_table(_database.logic.name_table(key))

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
        return self.sql.table(_database.logic.name_table(name), *columns)

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
        return self.sql.insert(table.name, *((_database.logic.column_name(table, col), value) for col, value in (*zip(table.columns, values), *columns.items())), id=id)

    def select(self, table: Table, *conditions: Condition, columns:tuple=("*",), all=True):
        """Select Columns from Table Where Conditions are Met"""
        conditions = (Condition("id", conditions[0]),) if len(conditions) == 1 and isinstance(
            conditions[0], int) else (_database.logic.condition_name(table, c, i) for i, c in enumerate(conditions))
        return self.sql.select(table.name, *conditions, columns=(_database.logic.column_name(table, col) for col in columns), all=all)

    def selectID(self, table: Table, *conditions: Condition, all=False):
        """Select ID from Table Where Conditions are Met"""
        conditions = (Condition("id", conditions[0]),) if len(conditions) == 1 and isinstance(
            conditions[0], int) else (_database.logic.condition_name(table, c, i) for i, c in enumerate(conditions))
        return self.sql.selectID(table.name, *conditions, all=all)

#-----------------------------------------------------------------------------#

__all__ = ["Database", "Type", "OP", "Table", "Column", "Condition"]
