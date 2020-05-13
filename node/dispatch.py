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
                self.data.data = res
                self.node._queues["handle"].put(self.data)
                return False
        elif end == False:
            def handle(self):
                res = func(self)
                self.data.data = res
                self.node._queues["handle"].put(self.data)
                return True
        else:
            def handle(self):
                res = func(self)
                self.data.data = res[1]
                self.node._queues["handle"].put(self.data)
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
        return self.data.data

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

    TIMEOUT = 1.0
    ATTEMPTS = 25

    def handle(self):
        if "CLIENT" in self.data.tags:
            self.client()
        else:
            self.server()

    def client(self):
        # Client tells server it is ready
        self.node.send(True, "ENCRYPT")
        # Client receives Common keys
        common = self.node.recv("ENCRYPT", Tag("COMMON"), wait=True)[0]
        base, modulus = map(int, common.data.split("|"))
        # Computes its key own using the private key
        mixture = base ** self.node._encrypt["private"] % modulus
        # Sends Server new key
        self.node.send(mixture, "DATA", "ENCRYPT", Tag("MIX"))
        # Recieves Server's new key
        mix = self.node.recv("ENCRYPT", Tag("MIX"), wait=True)[0]
        # Produces the Secret Key by mixing with own Private
        sk = int(mix.data) ** self.node._encrypt["private"] % modulus
        # Tell Server Secret has been computed
        self.node.send(True, "DATA", "ENCRYPT", Tag("WAIT"))
        self.node.join("send")
        self.node.recv("ENCRYPT", Tag("WAIT"), wait=True)
        # Wait until Server is also ready
        # Update Encryption Key
        self.node._encrypt["secret"] = sk
        # Send Server Heartbeat until Client receives confirmation they are both connected
        count = 0
        while count < self.ATTEMPTS:
            count += 1
            self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
            if self.node.recv("ENCRYPT", Tag("ENC"), wait=True, timeout=self.TIMEOUT):
                break
        else:
            raise error.CloseError(self.node)
        self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        # Send End to release lock
        self.node.send(True, "DATA", "ENCRYPT", Tag("END"))

    def server(self):
        base, modulus = self.node.server._encrypt["base"], self.node.server._encrypt["modulus"]
        # Sends Client Common keys
        self.node.send("{}|{}".format(base, modulus), "DATA", "ENCRYPT", Tag("COMMON"))
        # Computes its key own using the private key
        mixture = base ** self.node._encrypt["private"] % modulus
        # Sends Client new key
        self.node.send(mixture, "DATA", "ENCRYPT", Tag("MIX"))
        # Recieves Client's new key
        mix = self.node.recv("ENCRYPT", Tag("MIX"), wait=True)[0]
        # Produces the Secret Key by mixing with own Private
        sk = int(mix.data) ** self.node._encrypt["private"] % modulus
        # Tell Client Secret has been computed
        self.node.send(True, "DATA", "ENCRYPT", Tag("WAIT"))
        self.node.join("send")
        self.node.recv("ENCRYPT", Tag("WAIT"), wait=True)
        # Wait until Client is also ready
        # Update Encryption Key
        self.node._encrypt["secret"] = sk
        # Send Client Heartbeat until Server receives confirmation they are both connected
        count = 0
        while count < self.ATTEMPTS:
            count += 1
            self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
            if self.node.recv("ENCRYPT", Tag("ENC"), wait=True, timeout=self.TIMEOUT):
                break
        else:
            raise error.CloseError(self.node)
        self.node.send(True, "DATA", "ENCRYPT", Tag("ENC"))
        # Send End to release lock
        self.node.send(True, "DATA", "ENCRYPT", Tag("END"))

dispatch = {k:v for k,v in globals().items() if type(v) is type and k.upper() == k and v is not Dispatch and issubclass(v, Dispatch)}
