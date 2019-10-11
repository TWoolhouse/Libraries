import enum

@enum.unique
class Type(enum.Enum):
    AIPK = "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL"
    Integer = "INTEGER"
    TinyInt = "TINYINT"
    Bit = "BIT"
    String = "TEXT"
    Char = "CHAR"
    Date = "DATE"
    Bool = "BOOL"
    DateTime = "DATETIME"
    Time = "TIME"
    TimeStamp = "TIMESTAMP"
    Blob = "BLOB"
    PrimaryKey = "PRIMARY KEY"
    AutoIncrement = "AUTOINCREMENT"
    NotNull = "NOT NULL"

@enum.unique
class OP(enum.Enum):
    EQ = "="
    NE = "!="
    GT = ">"
    LT = "<"
    GE = ">="
    LE = "<="

    NOT = "NOT"
    AND = "AND"
    OR = "OR"
    PO = "("
    PC = ")"
    LIKE = "LIKE"
