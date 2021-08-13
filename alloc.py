class Allocator:
    def __init__(self, blocksize: int=16):
        assert int(blocksize) > 0, "Blocksize must be a non negative int"
        self.blocksize = max(1, int(blocksize))
        self.buffer: set[int] = {0}

    def __len__(self) -> int:
        return self.buffer.__len__()
    def __iter__(self):
        return self.buffer.__iter__()

    def aquire(self) -> int:
        key: int = 0
        count = 0
        while not key:
            key = next(iter(set(range(count * self.blocksize, (count + 1) * self.blocksize)) - self.buffer), 0)
            count += 1
        self.buffer.add(key)
        return key

    def release(self, key: int):
        self.buffer.discard(key)
