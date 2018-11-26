import socket
import _thread
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

    def __init__(self, addr="127.0.0.1", port=80, wrap_d=nullwrapper, wrap_e=nullwrapper, tunnel=False):
        self.addr, self.port, self.id, self.active, self.socket, self.encrypt, self.target = addr, port, -1, False, socket.socket(), False, False
        self.output_d, self.output_e = wrap_d(self.output_d), wrap_e(self.output_e)

    def __repr__(self):
        return "{} [{}:{}] : {}{}".format(self.id, self.addr, self.port, self.active, " "+str(self.target) if self.target else "")

    def __bool__(self):
        return self.id != -1

    def open(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.addr, self.port))
        except ConnectionRefusedError as e:
            return self.close(e)
        id = self.recv(16)
        self.id = int(id[1]) if id[0] == "ID" else -1
        if self.id != -1:
            self.active = True
            self.start_encryption()

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
            if self.data != None:
                self.handle()
        self.active = False

    def handle(self):
        if isinstance(self.data, Exception):
            return self.data
        elif self.data[0] == "PASS":
            pass
        elif self.data[0] == "CMD":
            try:
                command, args = self.data[1].split(" >> ", 1)
                args = args.split(" >> ")
                if (len(args) == 1) and (args[0] == "NULL"):    args = []
                try:    return getattr(self, command)(*args)
                except AttributeError:  pass
                if self.commands != None:
                    getattr(self.commands, command)(self, *args)
            except (IndexError, TypeError, AttributeError):
                return

        elif self.data[0] == "ERR":
            self.output_e()
        elif self.data[0] == "DATA":
            self.output_d()
    def output_d(self):
        return self.data[1]
    def output_e(self):
        return self.data[1]

    def cmd(self, command, *args, slv=False):
        self.send(("{} >> "+((("{} >> "*(len(args)-1))+"{}") if len(args) > 0 else "NULL")).format(command, *args), prefix="{}CMD".format("SLV" if slv else ""))

    def start_encryption(self):
        data = self.recv()
        if data[1] != "False":
            x = self.recv()[1]
            self.helman = {k : v for v,k in zip((int(i) for i in x.split(" - ")), ["g", "p"])}
            pk = secrets.randbelow(4096)
            self.send(self.helman["g"]**pk % self.helman["p"], "CRT")
            self.sk = (int(data[1])**pk % self.helman["p"]) % 256
            self.encrypt = True
        else:
            self.encrypt = False

    def connect(self, id):
        self.cmd("connect", id)
        data = self.recv()[1]
        self.target = int(id) if data == "True" else False
        return self.target

    def tunnel(self):
        pass
