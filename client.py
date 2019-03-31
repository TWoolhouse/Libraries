import socket
import _thread
import importlib
import secrets
import crypt
import hashes

def CON_ERR(func): # closes the socket if any network related errors occur
    def CON_ERR(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ConnectionError, OSError) as e:
            return args[0].close(e) # closes the socket if any network related errors occur
    return CON_ERR

class Client:

    def __init__(self, addr="127.0.0.1", port=80, commands=None, password=None, **funcs):
        """addr - IPv4 addr, port - port number, commands - The name of a module for the commands, funcs - the name of the prefix and the function to call when received"""
        self.addr = addr # IPv4 Address
        self.port = port # Port Number
        self.id = -1 # ID - -1 means the socket is inactive
        self.socket = socket.socket() # the socket object
        self.password = hashes.hmac(password, password) if password else None
        self.encrypt = False # weather to data is encrypted
        self.target = -1 # the ID of the target via the server
        self.funcs = {str(k).upper() : funcs[k] for k in funcs} # the functions that get called upon certain prefixes being received
        self.commands = None if commands == None else importlib.import_module(str(commands)) # the module that commands can be found in
        self._size = 4096
        self.received = [] # data that has been received and is not an in built prefix

    def __repr__(self):
        return str(self.socket)

    def __str__(self):
        return "{} [{}:{}]{}".format(self.id, self.addr, self.port, " -> "+str(self.target) if self.target != -1 else "")

    def __bool__(self):
        """Is False if the id is inactive so the connection is not up"""
        return self.id != -1

    def __enter__(self):
        self.open()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        return traceback

    def open(self):
        """Opens the socket and connects to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # makes the socket object
            self.socket.connect((self.addr, self.port)) # tries to connect to the server
        except (ConnectionRefusedError, OSError) as e:
            return self.close(e) # close the socket as it could not connect
        id = self.recv() # get the id from server
        print(id)
        self.id = int(id[1]) if id[0] == "ID" else -1 # check the id sent is an id
        print(self.id)
        if self: # if the id is valid (therefore there is a connection)
            self.encryption() # perform a diffe-helman if necessary
            if not self.password_check():
                raise ValueError("Incorrect Password")
            _thread.start_new_thread(self._recv_loop, tuple()) # start the recv_loop in a new thread so it is always listening
        else:
            return self.close(ConnectionRefusedError("Server sent no ID"))

    def close(self, err=None):
        """Closes connection with the Server"""
        try:
            self.id = -1 # to tell the recv_loop to stop
            self.socket.close() # close the socket connection
            return err # return an error if one was given
        except (ConnectionError, OSError) as e:
            raise # rasies an error if close is called twice in a row

    @CON_ERR
    def send(self, message, *prefixes): # message - What is being sent, prefixes - The prefixes e.g. BIN, RLY, PASS, CMD, ERR, DATA
        """Sends the data to the server with the prefixes for sorting the sent data"""
        print(message, *prefixes)
        prefixes = ("<"+"".join((str(i).upper() for i in prefixes))+">").encode("utf-8") # all the prefixes in uppercase in one string then encoded
        message = message if b"BIN" in prefixes else str(message).encode("utf-8") # the message is encoded if "BIN" is not found in the prefixes
        data = prefixes+message # adds the prefixes and message into one stream of bytes
        if self.encrypt: # if the data needs to be encrypted
            data = crypt.encode(data, self.sk, False) # bytes([i ^ self.sk for i in data]) # performs a XOR on the data using the private key
        print(data)
        self.socket.send(data) # sends the data to the server

    @CON_ERR
    def recv(self):
        """Recives the data from the Server and unpacks the data into prefixes and the message"""
        data = b""
        while data == b"": # makes sure the data is not empty
            data = self.socket.recv(self._size)
        print(data)
        if self.encrypt: # decrypts if necessary
            data = crypt.decode(data, self.sk, False) # bytes([i ^ self.sk for i in data])
        prefixes = data[1:data.index(b">")].decode("utf-8") # seperates the prefixes from the message
        message = data[data.index(b">")+1:] if "BIN" in prefixes else data[data.index(b">")+1:].decode("utf-8")
        return prefixes, message # returns a tuple with the prefixes and the message

    def _recv_loop(self):
        while self: # while the connection is active
            data = self.recv() # recv data
            _thread.start_new_thread(self.handle, (data,)) # make a new thread to handle the data so it can keep the recv_loop going

    def handle(self, data):
        if isinstance(data, Exception): # make sure the connection didn't errror
            return data # return the error
        elif data[0][:3] == "RLY": # if the data needs to be relayed
            self.send(data[1], data[0][3:]) # sends it on back to the server
        elif "PASS" in data[0]: # if prefix has "PASS" then do nothing
            pass
        elif "CMD" in data[0]: # if it's a command
            try:
                command, args = data[1].split(" >> ", 1) # splits up the command into command and args
                args = args.split(" >> ") # splits the args up seperataly
                if (len(args) == 1) and (args[0] == "NULL"):    args = [] # if there are no args, pass empty list
                try:    return getattr(self, command)(*args) # try Client functions
                except AttributeError:  pass # do nothing
                if self.commands != None: # only if there is a module
                    return getattr(self.commands, command)(self, *args) # call the function with arguments (passes self as it is not a member function)
            except (IndexError, TypeError, AttributeError) as e: # make sure the command exists
                return AttributeError("Command Not Found")
        else: # any other type of data
            self.received.append(data) # add it to the buffer
            try:    self.funcs[[prefix for prefix in self.funcs.keys() if prefix in data[0]][0]](self, data) # run the first function with the right prefix
            except IndexError:  pass

    def data(self, *prefixes, res=True):
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

    def password_check(self):
        data = self.data("PWD")[0]
        if data[1] == "True":
            pw = hashes.hmac(self.password, self.id)
            self.send(pw, "PWD", "BIN")
            return self.data("PWD")[0][1] == "True"
        return True

    def encryption(self):
        print("ENTCYPTION TIME")
        data = self.data("CRT") # recv the keys and g**B % p from the server
        self.helman = {k : v for k,v in zip(("g", "p"), (int(i) for i in data[1].split("-")))} # save the public keys
        if data[0] == "CRT" and data[1].split("-")[2] != "False": # if the server is setup for encryption
            pk = secrets.randbelow(4096) # generate a private key
            self.send(self.helman["g"]**pk % self.helman["p"], "CRT") # send g**A % p
            self.sk = (int(data[1].split("-")[2])**pk % self.helman["p"]) # calculate the shared private key
            self.encrypt = True # tell the Client to encrypt the data sent and received
        else:
            self.encrypt = False # tell the Client to not encrypt the data sent and received

    def relay(self, id):
        self.cmd("relay", id, prefixes="MKCON") # send the server the requested id of target
        if self.data("MKCON")[0][1] == "True": # see if it is valid
            self.target = id # set target to the id
        else:
            self.target = -1 # if it has failed, reset the target to -1 (fail state)
        return self.target != -1

    def tunnel(self): # TODO
        pass

    def size(self, val, other=None):
        self._size = int(val)
        if other:
            self.cmd("size", val)

    def cmd(self, command, *args, prefixes=""):
        self.send("{} >> {}".format(command, " >> ".join((str(a) for a in args)) if args else "NULL"), prefixes, "CMD")
