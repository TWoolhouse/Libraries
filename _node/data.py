class Data:

    def __init__(self, prefixes: iter, tags: iter, data: (str, bytes)):
        self.prefixes = [str(i).upper() for i in prefixes]
        self.tags = [str(i) for i in prefixes]
        self.data = data
