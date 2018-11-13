import socket
import _thread

def nullwrapper(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class Client:
    """Client that connects to a Server"""

    def __init__(self, addr, port, wrapper=nullwrapper):
        """IPv4 address, port number, wrapper to extract recvied data"""
        self.addr = addr
        self.port = port
        self.id = -1
        self.extract = wrapper(self.extract)

    def __repr__(self):
        return "ID: {}".format(self.id)

    def run(self):
        """Starts the connection and the main recive loop"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.addr, self.port))
            id = self.recv(16)
            self.id = int(id[1]) if id[0] == "<ID>" else -1
            if self.id == -1:
                raise ConnectionAbortedError("No valid ID sent by Server")
            self.active = True

            self.recv_loop()
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError):
            self.close()

    def send(self, message, prefix="DATA"):
        """Sends the message encoded in utf-8 with a prefix. Will automatically close the connection if an error is rasied."""
        try:
            self.socket.send("<{}>!~#~!{}".format(prefix.upper(), message).encode("utf-8")) #sends the var message encoded in utf-8
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError):
            self.close()

    def recv(self, size=4096):
        try:
            return self.socket.recv(size).decode("utf-8").strip().split("!~#~!") #recives decodes and strips any incoming messages
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError):
            self.close()

    def close(self):
        try:
            self.socket.close()
            self.active = False
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError) as e:
            print(e)

    def _recv_loop(self):
        while self.active:
            self.data = self.recv()
            if not self.data:
                self.active = False
                break
            self.active = self.handle_data()
        self.close()

    def recv_loop(self):
        _thread.start_new_thread(self._recv_loop, tuple())

    def stop(self):
        """Ends the current connection"""
        self.active = False
        self.close()

    def handle_data(self):
        if self.data[0] == "<DATA>":
            self.data = self.data[-1]
            self.extract()
            return True
        elif self.data[0] == "<CMD>":
            return True
        elif self.data[0] == "<ERR>":
            print(self.data[1])
            return True
        else:
            return False

    def extract(self):
        """Meant to be wrapped as this is the output of all DATA messages"""
        return self.data

    def isopen(self):
        """Returns True if the connection is currently open"""
        return self.active
