import enum

@enum.unique
class Mouse(enum.IntEnum):
    NONE = 0
    B1 = 1
    B2 = 3
    B3 = 2
    B4 = 4
    B5 = 5
    POS = 10
    WHEELUP = 11
    WHEELDOWN = 12