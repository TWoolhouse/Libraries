import socket
import _thread

def nullwrapper(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def CON_ERR(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ConnectionError, OSError) as e:
            return args[0].close(e)
    return wrapper

class Client:

    def __init__(self, addr="127.0.0.1", port=80, wrap_d=nullwrapper, wrap_e=nullwrapper):
        self.addr, self.port, self.id, self.active, self.socket = addr, port, -1, False, socket.socket()
        self.output_d, self.output_e = wrap_d(self.output_d), wrap_e(self.output_e)

    def __repr__(self):
        return "{} [{}:{}] : {}".format(self.id, self.addr, self.port, self.active, self.socket)

    def open(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.addr, self.port))
        except (ConnectionRefusedError, socket.timeout) as e:
            return self.close(e)
        id = self.recv(16)
        self.id = int(id[1]) if id[0] == "ID" else -1
        if self.id != -1:
            self.active = True
            _thread.start_new_thread(self.recv_loop, tuple())
        else:
            return self.close(ConnectionRefusedError("Server sent no ID"))

    def close(self, err=None):
        try:
            self.active = False
            self.id = -1
            self.socket.close()
            return err
        except (ConnectionError, OSError) as e:
            raise

    @CON_ERR
    def send(self, message, prefix="DATA", bin=False):
        if bin:
            self.socket.send(message) # sends the var message
        self.socket.send("<{}>{}".format(prefix.upper(), message).encode("utf-8")) # sends the var message encoded in utf-8
    @CON_ERR
    def recv(self, size=4096, bin=False):
        while True:
            data = self.socket.recv(size) # recives decodes and strips any incoming messages
            if not bin:
                data = data.decode("utf-8").strip()
                if data:
                    return data[1:].split(">", 1)
            else:
                return data

    def recv_loop(self):
        self.active = True
        while self.active:
            self.data = self.recv()
            if self.data != None:
                self.handle()
        self.active = False

    def handle(self):
        if isinstance(self.data, Exception):
            return self.data
        elif self.data[0] == "PASS":
            pass
        elif self.data[0] == "CMD":
            if self.data[1][:5] == "close":
                self.close(ConnectionAbortedError(self.data[1][6:-1]))
            else:
                pass # do client commands
        elif self.data[0] == "ERR":
            self.output_e()
        elif self.data[0] == "DATA":
            self.output_d()
    def output_d(self):
        return self.data[1]
    def output_e(self):
        return self.data[1]

    def cmd(self, command, *args):
        self.send(("{} >> "+((("{} >> "*(len(args)-1))+"{}") if len(args) > 0 else "NULL")).format(command, *args), prefix="CMD")
