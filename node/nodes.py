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
        self.event = threading.Event()
        self.func = self.threading(func)
        self.arg = func.__self__
        self.thread = threading.Thread(target=self.func, args=(self.arg, self.event))
    def start(self, event):
        self.event.set()
        self.event = event
        self.thread = threading.Thread(target=self.func, args=(self.arg, self.event))
        self.thread.start()
    def threading(self, func: callable) -> callable:
        @error.handle(error.CloseError, True, close=True)
        @error.log
        def threading(node, event):
            while event.is_set():
                func()
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

def _close_server_client(func, server):
    def _close(self):
        r = func(self)
        server.connections.discard(self)
        return r
    return _close

def clear_queue(q: queue.Queue):
    out = []
    try:
        while True:
            out.append(q.get(False))
            q.task_done()
    except queue.Empty:    pass
    return out

class Node:

    def __init__(self, c_socket: socket.socket, addr: str, port: int):
        self.c_socket = c_socket
        self.addr = addr
        self.port = port
        self.event = threading.Event()
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
        if not self.event.is_set():
            self.event = threading.Event()
            self.event.set()
            clear_queue(self._queues["send"])
            self._start()

    def close(self):
        try:
            self.event.clear()
            self.c_socket.close()
        except (ConnectionError, OSError):
            pass

    @property
    def errors(self):
        self._outputs["error"].extend(clear_queue(self._queues["error"]))
        return self._outputs["error"]

    def err(self, err: error.NodeBaseError) -> error.NodeBaseError:
        self._queues["error"].put(err)
        return err

    def _start(self):
        for thread in self._threads.values():
            thread.start(self.event)

    @error.handle(queue.Empty)
    def _thread_send(self):
        data = self._queues["send"].get(False)
        try:
            self._send(data)
        finally:
            self._queues["send"].task_done()

    def _thread_recv(self):
        old = b""
        while self:
            res = self._recv(old)
            if not res:
                continue
            data, old = res
            self._queues["recv"].put(data)

    def __bool__(self) -> bool:
        return self.event.is_set()

    def __repr__(self) -> str:
        return "[{}:{}] {}".format(self.addr, self.port, "X" if self else "O")

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

    def __init__(self, c_socket: socket.socket, addr: str, port: int, dispatchers=()):
        super().__init__(c_socket, addr, port)
        self._queues["handle"] = queue.Queue()
        self._threads["handle"] = Thread(self._thread_handle)
        self._outputs["data"] = []

        self._dispatchers =  {**self._dispatchers, **{d.__name__: d for d in dispatchers}}

    def send(self, data: (str, Data), *prefixes: str, tags: str=()):
        data = Data(data.data, *prefixes, *data.prefixes, tags=(*tags, *data.tags)) if isinstance(data, Data) else Data(data, *prefixes, tags=tags)
        self._queues["send"].put(data_send(data))

    @property
    def output(self):
        self._outputs["data"].extend(clear_queue(self._queues["handle"]))
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

    @error.handle(error.DispatchError)
    @error.log
    def _handle(self, data: Data):
        for prefix in data.prefixes:
            try:
                if not self._dispatchers[prefix](self, data).handle():
                    return False
            except KeyError:
                continue
        self._queues["handle"].put(data)

    @error.handle(queue.Empty)
    def _thread_handle(self):
        data = self._queues["recv"].get(False)
        try:
            self._handle(data_recv(data))
        finally:
            self._queues["recv"].task_done()

class Client(NodeClient):

    def __init_subclass__(cls, **kwargs):
        pass

    def __init__(self, addr: str, port: int, dispatch=()):
        super().__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM), addr, port, dispatch)

    @error.handle((ConnectionError, OSError), error.CloseError, close=True)
    @error.log
    def open(self):
        if not self:
            self.c_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.c_socket.connect((self.addr, self.port))
            super().open()

class ServerClient(NodeClient):

    def __init_subclass__(cls, **kwargs):
        pass

    def __init__(self, c_socket: socket.socket, addr: str, port: int, dispatchers=()):
        super().__init__(c_socket, addr, port, dispatchers)
        self.open()

    def open(self):
        super().open()
        print("Connection:", self)

class Server(Node):

    def __init__(self, addr: str, port: int, limit=10, client: ServerClient=ServerClient, dispatchers=()):
        super().__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM), addr, port)
        del self._queues["recv"], self._threads["recv"]
        self.limit = limit
        self.client = client
        self.dispatchers = dispatchers
        self.connections = set()

        self.client.close = _close_server_client(self.client.close, self)

    def open(self):
        self.c_socket.bind((self.addr, self.port))
        self.c_socket.listen(self.limit)
        super().open()

    def close(self, kill=True):
        super().close()
        if kill:
            for sc in list(self.connections):
                sc.close()

    @error.handle((ConnectionError, OSError), error.CloseError, close=True)
    def _thread_send(self):
        conn, addr = self.c_socket.accept()
        self.connections.add(self.client(conn, *addr, self.dispatchers))
