import socket
import _thread
import server_commands

def nullwrapper(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class Client:

    def __init__(self, c_socket, addr, server, wrapper):
        self.socket = c_socket
        self.addr = addr
        self.server = server
        server.count += 1
        self.id = server.count
        self.add_connection()
        self.send(self.id, "ID")
        self.extract = wrapper(self.extract)
        print("Connection from: " + repr(addr))
        self.active = True

        self.recv_loop()

    def __repr__(self):
        return "{} {}".format(self.id, self.addr)

    def add_connection(self):
        """Adds self to the list of connections on the Server"""
        self.server[self.id] = self

    def remove_connection(self):
        """Removes self off the list of connections to the Server"""
        del self.server[self.id]

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
            self.remove_connection()
            self.socket.close()
            self.active = 0
            print("{}: Connection Ended".format(self.addr))
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError) as e:
            print("ERROR!!!!! ",e)

    def _recv_loop(self):
        while self.active:
            self.data = self.recv()
            if not self.data:
                break
            self.handle_data()

    def recv_loop(self):
        _thread.start_new_thread(self._recv_loop, tuple())

    def stop(self):
        self.active = 0
        self.close()

    def handle_data(self):
        if self.data[0] == "<CMD>": #internal command
            start_index = self.data[1].index("(")
            self.data = [self.data[1][:start_index], self.data[1][start_index+1:]]
            self.data[1] = self.data[1][:-1] if len(self.data[1]) > 0 and self.data[1][-1] == ")" else self.data[1]
            try:
                getattr(server_commands, self.data[0])(self, *self.data[1].replace(", ", "[<]!~#~![>]").replace(",", "[<]!~#~![>]").split("[<]!~#~![>]"))
            except AttributeError as e:
                print("{} is not a recognised command".format(str(e)[42:]))
                self.send("IC", "ERR")
            except TypeError as e:
                print(e)
            return 1
        elif self.data[0] == "<DATA>":
            self.data = self.data[-1]
            self.extract()
            return 1
        else:
            self.close()

    def extract(self):
        """Meant to be wrapped as this is the output of all DATA messages"""
        return self.data

class Server:
    """Server that can take connections from Clients"""

    def __init__(self, addr, port, wrapper=nullwrapper):
        """IPv4 address, port number, wrapper to extract recvied data"""
        self.addr = addr
        self.port = port
        self.wrapper = wrapper
        self.connections = {}
        self.count = 0

    def __repr__(self):
        return "{}".format(self.connections)
    def __len__(self):
        return len(self.connections)
    def __iter__(self):
        return self.connections.__iter__()
    def __getitem__(self, key):
        return self.connections[key]
    def __setitem__(self, key, value):
        self.connections[key] = value
    def __delitem__(self, key):
        del self.connections[key]

    def run(self):
        """Starts the connection and the main listen loop"""
        self.connections = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.addr, self.port))
        self.socket.listen(10)
        print("Server listening for connections...\n")

        self.check()

    def _check(self):
        while self.active:
            try:
                c_socket, addr = self.socket.accept()
                _thread.start_new_thread(Client, (c_socket, addr, self, self.wrapper))
            except OSError:
                self.active = False

    def check(self):
        self.active = True
        _thread.start_new_thread(self._check, tuple())

    def stop(self):
        """Ends the current connection"""
        self.active = False
        self.socket.close()

    def send(self, client, message, prefix="DATA"):
        """Sends a message to a specific Client"""
        self.connections[client].send(message, prefix)

    def sendall(self, message, prefix="DATA"):
        """Sends all Clients a message"""
        for key in self:
            self.connections[key].send(message, prefix)
