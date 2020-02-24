__all__ = ["Table", "Column"]

from database.enums import Type, OP

def name_column(name: str) -> str:
    return name.lower().strip().replace(" ", "_")

def name_table(name: str) -> str:
    return "".join(i[0].upper()+i[1:] for i in name.strip().split())

class ID:
    def __init__(self, id):
        self._id = id
    
    @property
    def id(self):
        return self._id # or lookup the id if not exist

class Table(ID):
    pass

class Column(ID):

    def __init__(self, name: str, *types: Type, link: Table=None, id: int=0):
        super().__init__(id)
        self.name = name_column(name)
        self.types = types
        self.link = link

    def __repr__(self):
        return "{}<{} {}{}>".format(self._id, self.name, " ".join((i.value for i in self.types)), " -> {}".format(self.link) if self.link is not None else "")
    
    @classmethod
    def Foreign(cls, name: str, link: Table):
        return cls(name, Type.Integer, Type.NotNull, link=link)

class Table(ID):

    def __init__(self, name: str, *columns: Column, id: int=0):
        super().__init__(id)
        self.name = name_table(name)
        self.columns = columns
    
    def __repr__(self):
        return "{}<{} [{}]>".format(self._id, self.name, self.columns)

class Condition:

    def __init__(self, column: Column=None, value=None, operator: OP=OP.EQ):
        if column is None:
            self.name = "id"
            self.value = 0
            self.operator = OP.NE
        elif value is None:
            self.name = None
            self.value = column
            self.operator = operator
        else:
            self.name = column.name if isinstance(column, Column) else column
            self.value = value
            self.operator = operator

def column_name(table: Table, column) -> str:
    """
    column: Column, str, int
    """
    return column.name if isinstance(column, Column) else table.columns[column].name if isinstance(column, int) else column

def condition_name(table: Table, condition: Condition, index: int) -> Condition:
    if condition.name is None:
        condition.name = column_name(table, index)
    elif isinstance(condition.name, int):
        condition.name = column_name(table, condition.name)
    return condition
