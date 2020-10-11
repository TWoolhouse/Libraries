import enum

@enum.unique
class Type(enum.Enum):
    AIPK = "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL"
    INT = "INTEGER"
    TINY = "TINYINT"
    BIT = "BIT"
    STR = "TEXT"
    CHR = "CHAR"
    DATE = "DATE"
    BOOL = "BOOL"
    DATETIME = "DATETIME"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"
    BLOB = "BLOB"
    PK = "PRIMARY KEY"
    AUTO = "AUTOINCREMENT"
    NULL = "NOT NULL"

@enum.unique
class OP(enum.Enum):
    EQ = "=" # Equal
    NE = "!=" # Not Equal
    GT = ">" # Greater Than
    LT = "<" # Less Than
    GE = ">=" # Greater Than or Equal to
    LE = "<=" # Less Than or Equal to

    NOT = "NOT" # Not
    AND = "AND" # And
    OR = "OR" # Or
    PO = "(" # ( Parentheses Open
    PC = ")" # ) Parentheses Close
    LIKE = "LIKE" # Like
    IN = "IN" # In

class Join(enum.Enum):
    INNER = ""
    JOIN = INNER
    LEFT = "LEFT"
    RIGHT= "RIGHT"
    FULL = "FULL"
    OUTER = FULL