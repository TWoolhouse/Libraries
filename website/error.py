class WebsiteBaseError(Exception):
    pass

class TreeTraversal(WebsiteBaseError):

    def __init__(self, tree, request, segment, req=None):
        super().__init__()
        self.tree, self.request, self.segment, self.req = tree, request, segment, req

    def __str__(self) -> str:
        return f"{self.tree} > {self.request}[{self.segment}] {'' if self.req is None else self.req}"

class BufferRead(WebsiteBaseError):

    def __init__(self, buffer):
        super().__init__()
        self.buffer = buffer

    def __str__(self) -> str:
        return f"{self.buffer}"
