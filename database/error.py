class Database(Exception):
    pass

class Serialize(Database):
    def __init__(self, cls, msg="Serialization Failed"):
        self.cls = cls
        self.msg = msg

    def __str__(self) -> str:
        return f"'{self.cls}' {self.msg}"