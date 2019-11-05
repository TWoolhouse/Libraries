from _node.data import Data
from _node import error

def handle(func: callable, output, end):
    if output:
        if end == True:
            def handle(self):
                res = func(self)
                self.node.queues["handle"].put(res)
                return False
        elif end == False:
            def handle(self):
                res = func(self)
                self.node.queues["handle"].put(res)
                return True
        else:
            def handle(self):
                res = func(self)
                self.node.queues["handle"].put(res[1])
                return bool(res[0])
    else:
        if end == True:
            def handle(self):
                func(self)
                return False
        elif end == False:
            def handle(self):
                func(self)
                return True
        else:
            def handle(self):
                res = func(self)
                return bool(res)
    return handle

class Dispatch:

    def __init__(self, node, data: Data):
        self.node = node
        self.data = data

    def __init_subclass__(cls, output: bool=False, end: (bool, None)=True):
        cls.__init__ = super().__init__
        cls.handle = handle(cls.handle, output, end)

    def handle(self):
        raise error.DispatchError(self.node, self.__class__)

class PASS(Dispatch):

    def handle(self):
        pass

class CLOSE(Dispatch):

    def handle(self):
        self.node.close()

class ERR(Dispatch):

    def handle(self):
        self.node.err(error.RemoteError(self.node, self.data.data))

class CMD(Dispatch):
    pass

class CALL(Dispatch):
    pass

class RLY(Dispatch):
    pass

dispatch = {k:v for k,v in globals().items() if type(v) is type and k.upper() == k and v is not Dispatch and issubclass(v, Dispatch)}