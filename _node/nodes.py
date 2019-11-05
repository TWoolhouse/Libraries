from _node.data import Data
from _node import error
from _node import dispatch
import crypt
import hashes
import queue
import socket
import threading

_BUFFER_SIZE = 4096

class Thread:
    def __init__(self, func: callable):
        self.thread = threading.Thread(target=self.threading(func))
    def __bool__(self) -> bool:
        return self.thread.is_alive()
    def start(self):
        self.thread.start()
    def threading(self, func: callable) -> callable:
        @error.close_err
        @error.log_err
        @error.con_err
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
    return Data(pre, tag, data)

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

    def start(self):
        for thread in self._threads:
            if not thread:
                thread.start()

    def open(self):
        self.start()

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

    @error.que_err
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

    def __init__(self):
        super().__init__()
        self._queues["handle"] = queue.Queue()
        self._threads["handle"] = Thread(self._thread_handle)
        self._outputs["data"] = []

        self._dispatchers = {**dispatch.dispatch}

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

    def recv(self, prefixes: tuple, tags: tuple=(), wait: int=False) -> [Data]:
        results = [data for data in self.output if all(prefix in data.prefixes for prefix in prefixes) and all(tag in data.tags for tag in tags)]
        for res in results:
            self._outputs["data"].remove(res)
        while len(results) < wait:
            results.extend((data for data in self.output if all(prefix in data.prefixes for prefix in prefixes) and all(tag in data.tags for tag in tags)))
            for res in results:
                self._outputs["data"].remove(res)
        return results

    @error.con_err
    def _send(self, data: bytes):
        # self.encrypt
        self.c_socket.send(data+b"<|>")

    @error.con_err
    def _recv(self, raw=b"") -> (bytes, bytes):
        while b"<|>" not in raw:
            raw += self.c_socket.recv(_BUFFER_SIZE)
        data, old = raw.split(b"<|>", 1)
        # self.encrypt
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

    @error.que_err
    def _thread_handle(self):
        data = self._queues["recv"].get()
        self._handle(data_recv(data))
        self._queues["recv"].task_done()

class Client(NodeClient):
    pass
class ServerClient(NodeClient):
    pass
class Server(Node):
    pass
