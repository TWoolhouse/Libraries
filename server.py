import socket
import _thread
import importlib

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

    def __init__(self, addr, c_socket, server):
        self.addr, self.port, self.id, self.active, self.socket, self.server = addr[0], server.port, addr[1], False, c_socket, server
        self.output_d, self.output_e = server.wrap_d(self.output_d), server.wrap_e(self.output_e)
        self.send(self.id, "ID")
        self.server.add_connection(self)
        _thread.start_new_thread(self.recv_loop, tuple())
        print("Connection from [{}:{}] : {}".format(self.addr, self.port, self.id))

    def __repr__(self):
        return "[{}:{}]".format(self.addr, self.port, self.active, self.socket)

    def close(self, err=None):
        try:
            self.active = False
            self.server.remove_connection(self)
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
            if self.server.commands != None:
                try:
                    command, args = self.data[1].split(" >> ", 1)
                    args = args.split(" >> ")
                    if (len(args) == 1) and (args[0] == "NULL"):
                        args = []
                    getattr(self.server.commands, command)(self, *args)
                except IndexError:
                    self.send("INVALID CMD FORMAT", prefix="ERR")
                except AttributeError:
                    self.send("INVALID CMD", prefix="ERR")
                except TypeError:
                    self.send("INVALID ARG LEN", prefix="ERR")

        elif self.data[0] == "ERR":
            self.output_e()
        elif self.data[0] == "DATA":
            self.output_d()
    def output_d(self):
        return self.data[1]
    def output_e(self):
        return self.data[1]

class Server:

    def __init__(self, addr="", port=80, limit=10, wrap_d=nullwrapper, wrap_e=nullwrapper, commands=None):
        self.addr, self.port, self.limit, self.wrap_d, self.wrap_e, self.connections, self.active, self.socket, self.commands = addr, port, limit, wrap_d, wrap_e, {}, False, socket.socket(), importlib.import_module(str(commands)) if commands != None else None

    def __repr__(self):
        return "[{}:{}] {} : {}".format(self.addr, self.port, self.active, self.connections)

    def open(self):
        self.connections = {}
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.addr, self.port))
            self.socket.listen(self.limit)
        except ConnectionRefusedError as e:
            return self.close(e)
        _thread.start_new_thread(self.recv_loop, tuple())

    def close(self, err=None, end=True):
        try:
            self.active = False
            if end:
                for id in self.connections:
                    self.end(id, "Server Shutting Down")
            self.socket.close()
            return err
        except (ConnectionError, OSError) as e:
            raise

    @CON_ERR
    def recv_loop(self):
        self.active = True
        while self.active:
            c_socket, addr = self.socket.accept()
            _thread.start_new_thread(Client, (addr, c_socket, self))
        self.active = False

    def add_connection(self, cl):
        self.connections[cl.id] = cl
    def remove_connection(self, cl):
        del self.connections[cl.id]

    def send(self, id, message, prefix="DATA"):
        self.connections[id].send(message, prefix)
    def end(self, id, msg="Client Disconnected by Server"):
        self.send(id, "close("+msg+")", "CMD")
