import time

__all__ = ["DeltaTime"]

class DeltaTime:

    __value = 1/60
    __physics = 1/120
    __old = 0.0
    __new = 0.0
    __debt = __value

    @classmethod
    def value(cls):
        return cls.__value
    @classmethod
    def physics(cls):
        return cls.__physics
    @classmethod
    def time(cls):
        return cls.__now

    @classmethod
    def _next(cls):
        cls.__old = cls.__new
        cls.__new = time.time()
        cls.__value = cls.__new - cls.__old
        return cls.__value

    @classmethod
    def initialize(cls):
        cls._next()
        cls._next()
        cls.__debt = 1/60

    @classmethod
    def update(cls) -> bool:
        if cls.__debt < 0:
            time.sleep(abs(cls.__debt))
            cls.__debt = 0
        cls._next()
        cls.__debt += cls.__value - cls.__physics
        if cls.__debt > 1:
            cls.__debt = 0
        return cls.__debt <= 0

    dt = value
    ph = physics