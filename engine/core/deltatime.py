import time

__all__ = ["DeltaTime"]

class DeltaTime:
    """DeltaTime keeps track of time between each frame
    Can be used to create smooth framerate indepandant movement
    """

    __value = 1/60
    __physics = 1/120
    __old = 0.0
    __new = 0.0
    __debt = __value
    __max_frame_debt = 1.0

    @classmethod
    def value(cls) -> float:
        """Time between this frame and the last"""
        return cls.__value
    @classmethod
    def physics(cls) -> float:
        """A fixed value
        Denotes the time for each physics update
        """
        return cls.__physics
    @classmethod
    def time(cls) -> float:
        """Returns the current time in ms"""
        return cls.__now

    @classmethod
    def _next(cls) -> float:
        """Called once per frame to calculate the frame time"""
        cls.__old = cls.__new
        cls.__new = time.time()
        cls.__value = cls.__new - cls.__old
        return cls.__value

    @classmethod
    def initialize(cls):
        """Resets the times twice so ".value != .time" and is closer to 0
        It clears the time debt
        """
        cls._next()
        cls._next()
        cls.__debt = 1/60

    @classmethod
    def update(cls) -> bool:
        """Returns if we have enough time debt to render the scene this frame
        Only called once per frame/update cycle
        """
        if cls.__debt < 0: # Cap the debt to never go below 0
            time.sleep(-cls.__debt) # Pause for the debt so we don't run ahead
            cls.__debt = 0
        cls._next() # Update the internal values

        # Debt is frame_time - physics_time
        # if we don't render it will be negative bringing the debt below 0
        # This means we now have enough time to render
        cls.__debt += cls.__value - cls.__physics

        # Cap the debt so we don't run into never being able to render as the debt is too large
        if cls.__debt > cls.__max_frame_debt:
            cls.__debt = 0

        # Render if we have enough debt (includes if we overran)
        return cls.__debt <= 0

    dt = value
    ph = physics
