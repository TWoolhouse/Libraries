import random

__random = random.Random()

def load(rand, state=None):
    if not isinstance(rand, Random):
        raise ValueError("Must be of type Random")
    def load(func):
        def load(*args, **kwargs):
            rand.load(state)
            return func(*args, **kwargs)
        return load
    return load

def save(rand, after=True):
    if not isinstance(rand, Random):
        raise ValueError("Must be of type Random")
    def save(func):
        if after:
            def save(*args, **kwargs):
                return func(*args, **kwargs)
                rand.save()
        else:
            def save(*args, **kwargs):
                rand.save()
                return func(*args, **kwargs)
        return save
    return save


class Random(random.Random):
    def __init__(self, seed=None):
        super().__init__(seed)
        self.set()

    def load(self, state=None):
        self.setstate(self.rs_state if state == None else state)
        return self

    def save(self, state=None):
        self.rs_state = self.getstate() if state == None else state
        return self

    def set(self, state=None):
        self.save(state)
        self.load()
        return self

    def state(self):
        return self.rs_state

    def generate(self, value=4294967296):
        return self.randrange(value)

    def dload(self, state=None):
        load(self, state)

    def dsave(self, after=True):
        save(self, after)
