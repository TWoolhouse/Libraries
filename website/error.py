class WebsiteBaseError(Exception):
    pass

class TreeTraversal(WebsiteBaseError):
    
    def __init__(self, tree, request, segment, req=None):
        self.tree, self.request, self.segment, self.req = tree, request, segment, req

    def __str__(self) -> str:
        return f"{self.tree} > {self.request}[{self.segment}] {'' if self.req is None else self.req}"

class BufferRead(WebsiteBaseError):

    def __init__(self, buffer):
        self.buffer = buffer

    def __str__(self) -> str:
        return f"{self.buffer}"