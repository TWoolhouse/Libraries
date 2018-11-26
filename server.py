import socket
import _thread
import importlib
import secrets

def nullwrapper(func):
    def nullwrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return nullwrapper

def CON_ERR(func):
    def CON_ERR(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ConnectionError, OSError) as e:
            return args[0].close(e)
    return CON_ERR

class Client:

    def __init__(self, addr, c_socket, server):
        self.addr, self.port, self.id, self.active, self.socket, self.server, self.encrypt, self.target = addr[0], server.port, addr[1], False, c_socket, server, False, None
        self.output_d, self.output_e = server.wrap_d(self.output_d), server.wrap_e(self.output_e)
        self.server.add_connection(self)
        self.send(self.id, "ID")
        self.start_encryption()

        _thread.start_new_thread(self.recv_loop, tuple())

    def __repr__(self):
        return "[{}:{}]".format(self.addr, self.port, self.socket)

    def close(self, err=None):
        try:
            self.active = False
            self.socket.close()
            self.server.remove_connection(self)
            self.id = -1
            self.server.update()
            return err
        except (ConnectionError, OSError, KeyError) as e:
            raise

    @CON_ERR
    def send(self, message, prefix="DATA", bin=False, encrypt=None):
        encrypt = (self.encrypt if encrypt == None else encrypt)
        if not bin:
            message = "<{}>{}".format(prefix.upper(), message).encode("utf-8")
        if encrypt:
            message = bytes([i ^ self.sk for i in message])
        self.socket.send(message) # sends the var message
    @CON_ERR
    def recv(self, size=4096, bin=False, encrypt=None):
        encrypt = (self.encrypt if encrypt == None else encrypt)
        while True:
            data = self.socket.recv(size) # recives decodes and strips any incoming messages
            if encrypt:
                data = bytes([i ^ self.sk for i in data])
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
            if (self.data != None) and (not isinstance(self.data, Exception)):
                if (self.target != None) and (self.data[0][:3] == "SLV"):
                    self.target.send(self.data[1], self.data[0][3:])
                else:
                    self.handle()

    def handle(self):
        if self.data[0] == "PASS":
            pass
        elif self.data[0] == "CMD":
            try:
                command, args = self.data[1].split(" >> ", 1)
                args = args.split(" >> ")
                if (len(args) == 1) and (args[0] == "NULL"):    args = []
                try:    return getattr(self, command)(*args)
                except AttributeError:  pass
                if self.server.commands != None:
                    getattr(self.server.commands, command)(self, *args)
            except IndexError:      self.send("INVALID CMD FORMAT", prefix="ERR")
            except AttributeError:  self.send("INVALID CMD", prefix="ERR")
            except TypeError:       self.send("INVALID ARG LEN", prefix="ERR")
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

    def start_encryption(self):
        if self.server.encrypt:
            pk = secrets.randbelow(4096)
            self.send(self.server.helman["g"]**pk % self.server.helman["p"], "CRT")
            self.send(str(self.server.helman["g"])+" - "+str(self.server.helman["p"]), "CRT")
            self.sk = (int(self.recv()[1])**pk % self.server.helman["p"]) % 256
            self.encrypt = True
        else:
            self.send("False", "CRT")

    def connect(self, id):
        try:
            self.target = self.server.connections[int(id)]
        except KeyError:    self.target = None
        message = "False" if self.target == None else "True"
        self.send(message, "PASS")
        self.send(message, "PASS")

class Server:

    def __init__(self, addr="", port=80, limit=10, wrap_d=nullwrapper, wrap_e=nullwrapper, commands=None, encrypt=False):
        self.addr, self.port, self.limit, self.wrap_d, self.wrap_e, self.connections, self.active, self.socket, self.commands, self.encrypt = addr, port, limit, wrap_d, wrap_e, {}, False, socket.socket(), importlib.import_module(str(commands)) if commands != None else None, encrypt
        self.helman = {"g": get_prime(), "p":get_prime()}

    def __repr__(self):
        return "[{}:{}] {} : {}".format(self.addr if self.addr else "*.*.*.*", self.port, self.active, self.connections)

    def __getitem__(self, key):
        return self.connections[key]
    def __setitem__(self, key, value):
        self.connections[key] = value

    def open(self):
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

    def add_connection(self, cl):
        self.connections[cl.id] = cl
    def remove_connection(self, cl):
        del self.connections[cl.id]

    def send(self, id, message, prefix="DATA"):
        self.connections[id].send(message, prefix)
    def cmd(self, id, command, *args):
        self.connections[id].cmd(command, *args)
    def end(self, id, msg="Client Disconnected by Server"):
        self.cmd(id, "close", msg)
    def update(self, id=None):
        if id == None:
            for id in [i for i in self.connections]:
                self.send(id, "TEST", prefix="PASS")
        else:
            self.send(id, "TEST", prefix="PASS")

def get_prime():
    def is_prime(num):
        for i in range(2, (num+1)//2+1):
            if not num % i:
                return False
        return True
    num = secrets.randbelow(2048)
    while not is_prime(num):
        num = secrets.randbelow(2048)
    return num
