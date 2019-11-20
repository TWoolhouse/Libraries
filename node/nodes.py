from node.data import Data
from node import error
from node import dispatch
import crypt
import hashes
import queue
import socket
import threading

__all__ = ["Client", "ServerClient", "Server"]

BUFFER_SIZE = 4096

class Thread:
    def __init__(self, func: callable):
        self.thread = threading.Thread(target=self.threading(func))
    def __bool__(self) -> bool:
        return self.thread.is_alive()
    def start(self):
        self.thread.start()
    def threading(self, func: callable) -> callable:
        @error.log
        @error.handle(error.CloseError, True, close=True)
        @error.handle(error.DispatchError)
        def threading(node):
            while node:
                func(node)
        return threading

def data_send(data: Data) -> bytes:
    pre = "{}<#>{}<#>".format("|".join(data.prefixes), "|".join(data.tags)).encode("utf-8")
    data = data.data if isinstance(data.data, bytes) else data.data.encode("utf-8")
    return pre+data

def data_recv(data: bytes) -> Data:
    pre, tag, data = data.split(b"<#>", 2)
    pre = pre.decode("utf-8").split("|")
    tag = tag.decode("utf-8").split("|")
    data = data if b"BIN" in pre else data.decode("utf-8")
    return Data(data, *pre, tags=tag)

class Node:

    def __init__(self, c_socket: socket.socket, addr: str, port: int, id: int):
        self.c_socket = c_socket
        self.addr = addr
        self.port = port
        self.id = id
        self._queues = {
            "send": queue.Queue(),
            "recv": queue.Queue(),
            "error": queue.Queue()
            }
        self._threads = {
            "send": Thread(self._thread_send),
            "recv": Thread(self._thread_recv),
            }
        self._outputs = {
            "error": [],
            }

    def open(self):
        self._start()

    def close(self):
        try:
            self.id = -1
            self.c_socket.close()
        except (ConnectionError, OSError):
            pass

    @property
    def errors(self):
        try:
            while True:
                self._outputs["error"].append(self._queues["error"].get())
                self._queues["error"].task_done()
        except queue.Empty:
            pass
        return self._outputs["error"]

    def err(self, err: error.NodeBaseError) -> error.NodeBaseError:
        self._queues["error"].put(err)
        return err

    def _start(self):
        for thread in self._threads:
            if not thread:
                thread.start()

    @error.handle(queue.Empty, logging=False)
    def _thread_send(self):
        data = self._queues["send"].get()
        self._send(data)
        self._queues["send"].task_done()

    def _thread_recv(self):
        old = b""
        while self:
            data, old = self._recv(old)
            self._queues["recv"].put(data)

    def __bool__(self) -> bool:
        return self.id != -1

    # def __repr__(self) -> str:
    #     return ""

    # def __str__(self) -> str:
    #     return ""

    def __enter__(self):
        self.open()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        return self.close()

class NodeClient(Node):

    _dispatchers = dispatch.dispatch

    def __init_subclass__(cls, **kwargs):
        init_subclass = cls.__init_subclass__.__func__
        def _init_subclass(sub_cls, dispatchers={}, **sub_kwargs):
            sub_cls._dispatchers = {**super(cls, cls)._dispatchers, **sub_cls._dispatchers, **dispatchers}
            init_subclass(sub_cls, **sub_kwargs)
        cls.__init_subclass__ = classmethod(_init_subclass)

    def __init__(self, c_socket: socket.socket, addr: str, port: int, id: int, dispatchers={}):
        super().__init__(c_socket, addr, port, id)
        self._queues["handle"] = queue.Queue()
        self._threads["handle"] = Thread(self._thread_handle)
        self._outputs["data"] = []

        self._dispatchers =  {**self._dispatchers, **dispatchers}

    def send(self, data: Data):
        self._queues["send"].put(data_send(data))

    @property
    def output(self):
        try:
            while True:
                self._outputs["data"].append(self._queues["handle"].get())
                self._queues["handle"].task_done()
        except queue.Empty:    pass
        return self._outputs["data"]

    def recv(self, *prefixes, tags: tuple=(), wait: int=False) -> [Data,]:
        results = [data for data in self.output if all(prefix in data.prefixes for prefix in prefixes) and all(tag in data.tags for tag in tags)]
        for res in results:
            self._outputs["data"].remove(res)
        while len(results) < wait:
            results.extend((data for data in self.output if all(prefix in data.prefixes for prefix in prefixes) and all(tag in data.tags for tag in tags)))
            for res in results:
                self._outputs["data"].remove(res)
        return results

    @error.handle((ConnectionError, OSError), error.CloseError, close=True)
    def _send(self, data: bytes):
        crypt.encrypt_bytes(data, b"encryption")
        self.c_socket.send(data+b"<|>")

    @error.handle((ConnectionError, OSError), error.CloseError, close=True)
    def _recv(self, raw=b"") -> (bytes, bytes):
        while b"<|>" not in raw:
            raw += self.c_socket.recv(BUFFER_SIZE)
        data, old = raw.split(b"<|>", 1)
        crypt.decrypt_bytes(data, b"encryption")
        return data, old

    def _handle(self, data: Data):
        for prefix in data.prefixes:
            try:
                if not self._dispatchers[prefix](self, data):
                    return False
            except KeyError:
                continue
        self._queues["handle"].put(data)

    def _append(self, data: Data):
        if "CLR" not in data.prefixes:
            self._queues["handle"].put(data)

    @error.handle(queue.Empty, logging=False)
    def _thread_handle(self):
        data = self._queues["recv"].get()
        self._handle(data_recv(data))
        self._queues["recv"].task_done()

class Client(NodeClient):

    def __init_subclass__(cls, **kwargs):
        pass

    def __init__(self, addr: str, port: int, dispatch={}):
        super().__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM), addr, port, -1, dispatch)

    @error.handle((ConnectionError, OSError), error.CloseError, close=True)
    def open(self):
        self.c_socket.connect((self.addr, self.port))
        self.id = 0
        super().open()

class ServerClient(NodeClient):

    def __init_subclass__(cls, **kwargs):
        pass

    def __init__(self, c_socket: socket.socket, addr: str, port: int, id: int, dispatchers={}):
        super().__init__(c_socket, addr, port, id, dispatchers)
        self.open()

class Server(Node):

    def __init__(self, addr: str, port: int, limit=10, client: ServerClient=ServerClient, dispatchers={}):
        super().__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM), addr, port, -1)
        del self._queues["send"], self._threads["send"]
        self.limit = limit
        self.client = client
        self.dispatchers = dispatchers

    def open(self):
        self.c_socket.bind((self.addr, self.port))
        self.id = 0
        self.c_socket.listen(self.limit)
        super().open()

    def close(self):
        super().close()

    def _thread_recv(self):
        conn, addr = self.c_socket.accept()
        self.client(conn, *addr, conn.fileno(), self.dispatchers)
