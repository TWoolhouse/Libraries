import enum

class Status(enum.IntEnum):
    NONE = 0
    QUEUE = 1
    ACTIVE = 2
    DONE = 3
    SKIP = 4
    CLEAR = 5
    INVALID = 6