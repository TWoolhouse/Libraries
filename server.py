import socket
import _thread
import importlib
import secrets

def CON_ERR(func): # closes the socket if any network related errors occur
    def CON_ERR(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ConnectionError, OSError) as e:
            return args[0].close(e) # closes the socket if any network related errors occur
    return CON_ERR

class Client:

    def __init__(self, addr, c_socket, server):
        self.addr = addr[0] # IPv4 Address
        self.port = server.port # Port Number
        self.id = addr[1] # ID - -1 means the socket is inactive
        self.socket = c_socket # the socket object
        self.server = server # weather to data is encrypted
        self.target = -1
        self.size = 4096
        self.received = [] # data that has been received and is not an in built prefix

        self.server.add_connection(self)
        self.send(self.id, "ID") # sends the ID of the Client for setup
        self.encryption()

        self.recv_loop()

    def __repr__(self):
        return "{} [{}:{}]{}".format(self.id, self.addr, self.port, " -> "+str(self.target) if self.target != -1 else "")

    def __bool__(self):
        """Is False if the id is inactive so the connection is not up"""
        return self.id != -1

    def close(self, err=None):
        """Closes connection with the Client"""
        try:
            self.id = -1 # to tell the recv_loop to stop
            self.socket.close() # close the socket connection
            self.server.remove_connection() # remove any invalid connections
            self.server.update() # remove any invalid connections
            return err # return an error if one was given
        except (ConnectionError, OSError) as e:
            raise Exception("WELL THIS DIDN'T GO WELL")# rasies an error if close if called twice in a row

    @CON_ERR
    def send(self, message, *prefixes): # message - What is being sent, prefixes - The prefixes e.g. BIN, RLY, PASS, CMD, ERR, DATA
        """Sends the data to the server with the prefixes for sorting the sent data"""
        prefixes = ("<"+"".join((str(i).upper() for i in prefixes))+">").encode("utf-8") # all the prefixes in uppercase in one string then encoded
        message = message if b"BIN" in prefixes else str(message).encode("utf-8") # the message is encoded if "BIN" is not found in the prefixes
        data = prefixes+message # adds the prefixes and message into one stream of bytes
        if self.server.encrypt: # if the data needs to be encrypted
            data = bytes([i ^ self.sk for i in data]) # performs a XOR on the data using the private key
        self.socket.send(data) # sends the data to the Client
    @CON_ERR
    def recv(self):
        """Recives the data from the Client and unpacks the data into prefixes and the message"""
        data = b""
        while data == b"": # makes sure the data is not empty
            data = self.socket.recv(self.size)
        if self.server.encrypt: # decrypts if necessary
            data = bytes([i ^ self.sk for i in data])
        prefixes = data[1:data.index(b">")].decode("utf-8") # seperates the prefixes from the message
        message = data[data.index(b">")+1:] if "BIN" in prefixes else data[data.index(b">")+1:].decode("utf-8")
        return prefixes, message # returns a tuple with the prefixes and the message

    def recv_loop(self):
        while self: # while the connection is active
            data = self.recv() # recv data
            _thread.start_new_thread(self.handle, (data,)) # make a new thread to handle the data so it can keep the recv_loop going

    def handle(self, data):
        if isinstance(data, Exception): # make sure the connection didn't errror
            return data # return the error
        elif data[0][:3] == "RLY": # if the data needs to be relayed
            if self.target != -1 and self.target.id != -1: # checks to see if it has a target and if it is still open
                self.target.send(data[1], data[0][3:]) # sends it on to the target Client
            else:   self.cmd("relay", "-1") # tell the Client to reset their target
        elif "PASS" in data[0]: # if prefix has "PASS" then do nothing
            pass
        elif "CMD" in data[0]: # if it's a command
            try:
                command, args = data[1].split(" >> ", 1) # splits up the command into command and args
                args = args.split(" >> ") # splits the args up seperataly
                if (len(args) == 1) and (args[0] == "NULL"):    args = [] # if there are no args, pass empty list
                try:    return getattr(self, command)(*args) # try Client functions
                except AttributeError:  pass # do nothing
                if self.server.commands != None: # only if there is a module
                    return getattr(self.server.commands, command)(self, *args) # call the function with arguments (passes self as it is not a member function)
            except (IndexError, TypeError, AttributeError) as e: # make sure the command exists
                return AttributeError("Command Not Found")
        else: # any other type of data
            self.received.append(data) # add it to the buffer
            try:    self.server.funcs[[prefix for prefix in self.server.funcs.keys() if prefix in data[0]][0]](self, data) # run the first function with the right prefix
            except IndexError:  pass

    def data(self, *prefixes, res=False):
        if res: # if we will wait for a response with the required prefixes
            while True: # wait forever
                messages = [message for message in self.received if all([prefix.upper() in message[0] for prefix in prefixes])] # check the messages
                if messages != []: # if some were found
                    break # end the loop
        else:
            messages = [message for message in self.received if all([prefix.upper() in message[0] for prefix in prefixes])] # grab whatever fits the bill
        for message in messages: # remove all of the chosen messages from the buffer
            self.received.remove(message)
        return messages # return the chosen messages

    def encryption(self):
        pk = secrets.randbelow(4096) # generate a private key
        self.send("-".join((str(self.server.helman["g"]), str(self.server.helman["p"]), str(self.server.helman["g"]**pk % self.server.helman["p"]) if self.server.encrypt else "False")), "CRT") # sends the public keys and g**B % p if the server is setup to encrypt
        if self.server.encrypt: # if the server is set to encrypt wait for the key from Client
            data = self.recv() # recv g**A % p from the Client
            if data[0] == "CRT":
                self.sk = (int(data[1])**pk % self.helman["p"]) % 256 # calculate the shared private key
            else:
                self.close() # close if you do not recv the key

    def relay(self, id):
        try:    id = int(id) # check the id is a num
        except ValueError:
            self.send("False", "MKCON") # send False to tell the Client this has failed
            self.target = -1 # tell the server we have no connection
        if id in self.server.connections: # if the id is valid
            self.send("True", "MKCON") # send True
            self.target = self.server.connections[id] # tell the sever we have a connection
        else:
            self.send("False", "MKCON") # send False to tell the Client this has failed
            self.target = -1 # tell the server we have no connection

    def cmd(self, command, *args, prefixes=""):
        self.send("{} >> {}".format(command, " >> ".join((str(a) for a in args)) if args else "NULL"), "CMD", prefixes)

class Server:

    def __init__(self, addr="", port=80, limit=10, commands=None, encrypt=False, **funcs):
        self.addr = addr # IPv4 Address
        self.port = port # Port Number
        self.limit = limit # Number of max connections
        self.funcs = {str(k).upper() : funcs[k] for k in funcs} # the functions that get called upon certain prefixes being received
        self.commands = None if commands == None else importlib.import_module(str(commands)) # the module that commands can be found in
        self.encrypt = encrypt # Whether the Server will encrpyt the data sent
        self.helman = {"g": 1, "p":1}
        self.connections = {} # A dictionary to hold the Client objects when they are active
        self.socket = socket.socket()
        self.active = False # Whether the Server is accepting connections

    def __repr__(self):
        return "[{}:{}] {} :{}".format(self.addr if self.addr else "*.*.*.*", self.port, self.active, "\n\t"+("\n\t".join((str(i) for i in self.connections.values()))))

    def __getitem__(self, key):
        return self.connections[key]
    def __setitem__(self, key, value):
        self.connections[key] = value
    def __iter__(self):
        return self.connections.__iter__()

    def open(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.addr, self.port))
            self.socket.listen(self.limit)
        except (ConnectionRefusedError, OSError) as e:
            return self.close(e)
        self.active = True

        _thread.start_new_thread(self.recv_loop, tuple())

    def close(self, err=None, end=True):
        try:
            self.active = False
            self.socket.close()
            if end:
                for id in self.connections:
                    self.connections[id].close()
            return err
        except (ConnectionError, OSError) as e:
            raise

    @CON_ERR
    def recv_loop(self):
        while self:
            c_socket, addr = self.socket.accept()
            _thread.start_new_thread(Client, (addr, c_socket, self))

    def add_connection(self, cl):
        self.connections[cl.id] = cl
    def remove_connection(self, cl=None):
        if cl != None:
            del self.connections[cl]
        else:
            for i in [j for j in self.connections]:
                if self.connections[i].id == -1:
                    del self.connections[i]

    def send(self, id, message, *prefixes):
        self.connections[id].send(message, *prefixes)
    def cmd(self, id, command, *args, prefixes=""):
        self.connections[id].cmd(message, *args, prefixes=prefixes)
    def end(self, id):
        self.connections[id].close()
    def update(self):
        for cl in [i for i in self.connections]:
            self.connections[cl].send("PASS", "PASS")
