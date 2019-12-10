from node.data import Data, Tag
from node import error
import time

__all__ = ["Dispatch"]

class Node: pass

def handle(func: callable, output, end):
    if output:
        if end == True:
            def handle(self):
                res = func(self)
                self.node._queues["handle"].put(res)
                return False
        elif end == False:
            def handle(self):
                res = func(self)
                self.node._queues["handle"].put(res)
                return True
        else:
            def handle(self):
                res = func(self)
                self.node._queues["handle"].put(res[1])
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

    def __init__(self, node: Node, data: Data):
        self.node = node
        self.data = data

    def __init_subclass__(cls, output: bool=False, end: (bool, None)=True, node: Node=None):
        cls.__name__ = cls.__name__.upper()
        if super(cls, cls).__init__ != cls.__init__:
            cls.__init__ = super(cls, cls).__init__
        cls.handle = handle(error.dispatch(cls.handle), output, end)
        if node is not None:
            node._dispatchers[cls.__name__] = cls

    def handle(self):
        raise TypeError("Not a Valid Dispatcher")

class DATA(Dispatch, output=True):

    def handle(self):
        return self.data

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

class ENCRYPT(Dispatch):

    def handle(self):
        if "CLIENT" in self.data.tags:
            self.client()
        else:
            self.server()

    def client(self):
        self.node.send(True, "ENCRYPT")
        common = self.node.recv("ENCRYPT", Tag("COMMON"), wait=True)[0]
        base, modulus = map(int, common.data.split("|"))
        mixture = base ** self.node._encrypt["private"] % modulus
        self.node.send(mixture, "DATA", "ENCRYPT", Tag("MIX"))
        mix = self.node.recv("ENCRYPT", Tag("MIX"), wait=True)[0]
        sk = int(mix.data) ** self.node._encrypt["private"] % modulus
        self.node.send(True, "DATA", "ENCRYPT", Tag("WAIT"))
        self.node.join("send")
        self.node.recv("ENCRYPT", Tag("WAIT"), wait=True)
        self.node._encrypt["secret"] = sk
        self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        while not self.node.recv("ENCRYPT", Tag("ENC"), wait=True, timeout=0.75):
            self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        self.node.send(True, "DATA", "ENCRYPT", Tag("END"))

    def server(self):
        base, modulus = self.node.server._encrypt["base"], self.node.server._encrypt["modulus"]
        self.node.send("{}|{}".format(base, modulus), "DATA", "ENCRYPT", Tag("COMMON"))
        mixture = base ** self.node._encrypt["private"] % modulus
        self.node.send(mixture, "DATA", "ENCRYPT", Tag("MIX"))
        mix = self.node.recv("ENCRYPT", Tag("MIX"), wait=True)[0]
        sk = int(mix.data) ** self.node._encrypt["private"] % modulus
        self.node.send(True, "DATA", "ENCRYPT", Tag("WAIT"))
        self.node.join("send")
        self.node.recv("ENCRYPT", Tag("WAIT"), wait=True)
        self.node._encrypt["secret"] = sk
        self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        while not self.node.recv("ENCRYPT", Tag("ENC"), wait=True, timeout=0.75):
            self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        self.node.send(True, "DATA", "ENCRYPT", Tag("END"))

dispatch = {k:v for k,v in globals().items() if type(v) is type and k.upper() == k and v is not Dispatch and issubclass(v, Dispatch)}
