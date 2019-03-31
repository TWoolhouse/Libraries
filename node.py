import crypt
import hashes
import importlib
import queue
import socket
import threading

def con_err(func): # closes the socket if any network related errors occur
    def con_err(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (ConnectionError, OSError) as e:
            return self.close(e) # closes the socket if any network related errors occur
    return con_err

def con_active(func): # if the socket is open
    def con_active(self, *args, **kwargs):
        if self.id != -1:
            return func(self, *args, **kwargs)
    return con_active

def log_err(func): # add the error to the queue then re-raise the error
    def log_err(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.err(e)
            raise
    return log_err

class CloseError(Exception):
    pass

class Node:

    def __init__(self, c_socket, addr="127.0.0.1", port=80, id=-1, password=None, encrypt=0, funcs={}, commands=None, size=4096, workers={"handle":1}):
        self.addr = addr # IPv4 Address
        self.port = port # Port Number
        self.id = id # ID -1 means the socket is inactive
        self.socket = c_socket # the socket object
        self._size = size # max size per recv

        self.security = {
        "password": hashes.hmac(password, password) if password else None, # Password for the initial connection
        "encrypt": encrypt, # The secret key for encryption, if any
        }

        self.commands = {
        "internal": {str(k).upper() : funcs[k] for k in funcs}, # the functions that get called upon certain prefixes being received
        "external": commands if type(commands).__name__ == "module" else (importlib.import_module(str(commands)) if commands else None), # the module that commands can be found in
        }

        self.queues = { # Queues
        "received": queue.Queue(), # data that has been received
        "errors": queue.Queue(), # errors found in threads that have been caught
        }
        self.threads = { # Threads controled by the client
        "recv_loop": None, # worker for the recv loop
        "handles": []
        }
        self.workers = workers # max number of workers per task

    def __repr__(self):
        return "{}\n\nSecurity: {}\nCommands: {}\nQueues: {}\nWorkers: {}\nThreads: {} - {}".format(
        self.__str__(),
        self.security,
        self.commands,
        {k : self.queues[k].qsize() for k in self.queues},
        self.workers,
        sum((len((True for i in self.threads[k] if i.is_alive())) if type(self.threads[k]) == list else int(self.threads[k].is_alive()) for k in self.threads if k != "workers")),
        {k : ["{}-{}".format(i.name, int(i.is_alive())) for i in self.threads[k]] if type(self.threads[k]) == list else "{}-{}".format(self.threads[k].name, int(self.threads[k].is_alive())) for k in self.threads if k != "workers"}
        )
    def __str__(self):
        return "[{}:{}] {} @ {}B".format(
        self.addr,
        self.port,
        self.id,
        self._size
        )
    def __bool__(self):
        """Is False if the id is inactive so the connection is not up"""
        return self.id != -1

    def err(self, err):
        self.queues["errors"].put(err)
        return err

    def start(self):
        """Starts up the threads and setup functions"""
        self.threads["recv_loop"] = threading.Thread(target=self._worker_recv_loop, daemon=True)
        self.threads["handles"] = [threading.Thread(target=self._worker_handle, daemon=True) for i in range(self.workers["handle"])]
        self.threads["recv_loop"].start()
        for tl in ("handles",):
            for t in self.threads[tl]:
                t.start()

    def open(self):
        self.start()

    @log_err
    def close(self, err=CloseError()):
        """Closes the connection and ends threads"""
        self.id = -1 # to tell the recv_loop to stop
        try:
            self.socket.close() # close the socket connection
        except (ConnectionError, OSError) as e:
            raise # rasies an error if close is called twice in a row
        return err # return an error if one was given

    def _worker_recv_loop(self):
        pass
    def _worker_handle(self):
        pass

class NodeClient(Node):

    def __init__(self, *args, workers={"handle":1, "process":1}, **kwargs):
        super().__init__(*args, workers=workers, **kwargs)
        self.handled = [] # data that has been handled and is not an in-built prefix
        self.target = -1 # the ID of the target via the server
        self.queues["processes"] = queue.Queue() # processes that have been requested to be called
        self.threads["processes"] = []

    def __repr__(self):
        return "{}\n\nSecurity: {}\nCommands: {}\nQueues: {}\nWorkers: {}\nThreads: {} - {}\nHandled: {}".format(
        self.__str__(),
        self.security,
        self.commands,
        {k : self.queues[k].qsize() for k in self.queues},
        self.workers,
        sum((len([True for i in self.threads[k] if i.is_alive()]) if type(self.threads[k]) == list else int(self.threads[k].is_alive()) for k in self.threads)),
        {k : ["{}-{}".format(i.name, int(i.is_alive())) for i in self.threads[k]] if type(self.threads[k]) == list else "{}-{}".format(self.threads[k].name, int(self.threads[k].is_alive())) for k in self.threads},
        self.handled
        )
    def __str__(self):
        return "[{}:{}] {} -> {} @ {}B".format(
        self.addr,
        self.port,
        self.id,
        self.target,
        self._size
        )

    def process(self, cmd, *args, **kwargs):
        self.queues["processes"].put((cmd, args, kwargs))

    def start(self):
        super().start()
        self.threads["processes"] = [threading.Thread(target=self._worker_process, daemon=True) for i in range(self.workers["process"])]
        for t in self.threads["processes"]:
            t.start()

    @con_err
    @log_err
    def send(self, message, *prefixes): # message - What is being sent, prefixes - The prefixes e.g. BIN, RLY, PASS, CMD, ERR, DATA
        """Sends the data to the server with the prefixes for sorting the sent data"""
        prefixes = ("<"+"|".join((str(i).upper() for i in prefixes))+">").encode("utf-8") # all the prefixes in uppercase in one string then encoded
        message = message if b"BIN" in prefixes else str(message).encode("utf-8") # the message is encoded if "BIN" is not found in the prefixes
        data = prefixes+message # adds the prefixes and message into one stream of bytes
        if self.security["encrypt"]: # if the data needs to be encrypted
            data = crypt.encode(data, self.security["encrypt"], False) # performs a XOR on the data using the private key
        self.socket.send(data) # sends the data to the server

    @con_err
    @log_err
    def recv(self):
        """Recives the data from the Server and unpacks the data into prefixes and the message"""
        data = b""
        while data == b"": # makes sure the data is not empty
            data = self.socket.recv(self._size)
        if self.security["encrypt"]: # decrypts if necessary
            data = crypt.decode(data, self.security["encrypt"], False) # performs a XOR on the data using the private key
        prefixes = data[1:data.index(b">")].decode("utf-8") # seperates the prefixes from the message
        message = data[data.index(b">")+1:] if "BIN" in prefixes else data[data.index(b">")+1:].decode("utf-8")
        return prefixes, message # returns a tuple with the prefixes and the message

    @log_err
    def handle(self, data):
        if data[0][:3] == "RLY": # if the data needs to be relayed
            self.process(self.send, data[1], data[0][3:]) # sends it on back to the server
        elif "PASS" in data[0]: # if prefix has "PASS" then do nothing
            return None
        elif "CMD" in data[0]: # if it's a command
            try:
                command, args = data[1].split(" >> ", 1) # splits up the command into command and args
                args = args.split(" >> ") # splits the args up seperataly
                if (len(args) == 1) and (args[0] == "NULL"):    args = [] # if there are no args, pass empty list
                try:    return self.process(getattr(self, command), *args) # try Client functions
                except AttributeError:  pass # do nothing
                if self.commands["external"] != None: # only if there is a module
                    return self.process(getattr(self.commands["external"], command), self, *args) # call the function with arguments (passes self as it is not a member function)
            except (IndexError, TypeError, AttributeError) as e: # make sure the command exists
                return self.err(AttributeError("Command Not Found"))
        else: # any other type of data
            try:    self.process(self.commands["internal"][[prefix for prefix in self.commands["internal"].keys() if prefix in data[0]][0]], self, data) # run the first function with the right prefix
            except IndexError:  self.handled.append(data) # add it to the buffer

    def data(self, *prefixes, res=False):
        while res: # if we will wait for a response with the required prefixes
            messages = [message for message in self.handled if all([prefix.upper() in message[0] for prefix in prefixes])] # check the messages
            if messages != []: # if some were found
                break # end the loop
        else:
            messages = [message for message in self.handled if all([prefix.upper() in message[0] for prefix in prefixes])] # grab whatever fits the bill
        for message in messages: # remove all of the chosen messages from the buffer
            self.handled.remove(message)
        return messages # return the chosen messages

    def _worker_recv_loop(self):
        while self.id != -1: # while the connection is active
            data = self.recv() # recv data
            if isinstance(data, Exception): # make sure the connection didn't errror
                self.err(data)
            else:
                self.queues["received"].put(data) # add the data to the queue to be handled by another thread

    def _worker_handle(self):
        while self.id != -1: # while the connection is active
            try:
                data = self.queues["received"].get(timeout=1) # request data from the unprocessed data queue
                if data:
                    self.handle(data) # handle the data
                self.queues["received"].task_done() # tell queue the task has been processed
            except queue.Empty: pass

    def _worker_process(self):
        while self.id != -1: # while the connection is active
            try:
                process = self.queues["processes"].get(timeout=1)
                if process:
                    process[0](*process[1], **process[2]) # call the function with the params
                self.queues["processes"].task_done()
            except queue.Empty: pass

class Client(NodeClient):

    def __init__(self, addr="127.0.0.1", port=80, id=-1, password=None, encrypt=0, funcs={}, commands=None, size=4096, workers={"handle":1, "process":1}):
        super().__init__(socket.socket(), addr, port, id, password, encrypt, funcs, commands, size, workers=workers)

    @log_err
    def open(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # makes the socket object
            self.socket.connect((self.addr, self.port)) # tries to connect to the server
        except (ConnectionRefusedError, OSError) as e:
            raise self.close(e) # close the socket as it could not connect
        id = self.recv() # get the id from server
        self.id = int(id[1]) if id[0] == "ID" else -1 # check the id sent is an id
        if self.id != -1: # if the id is valid (therefore there is a connection)
            super().open()
        else:
            raise ConnectionRefusedError("Server sent no ID")

class SClient(NodeClient):

    def __init__(self, c_socket, addr, server, workers):
        super().__init__(c_socket, addr[0], server.port, addr[1],
        server.security["password"], server.security["encrypt"],
        server.commands["internal"], server.commands["external"], server._size, workers=workers)
        self.server = server
        self.open()

    @log_err
    def open(self):
        self.server._add_connection(self)
        self.send(self.id, "ID")
        super().open()

    def close(self, err=CloseError()):
        id = self.id
        super().close(err)
        self.server._remove_connection(id)

class Server(Node):

    def __init__(self, addr="", port=80, limit=10, password=None, encrypt=0, commands=None, workers={"handle":1, "c_handle":1, "c_process":1}, **funcs):
        super().__init__(socket.socket(), addr, port, password=password, encrypt=encrypt, funcs=funcs, commands=commands, workers=workers)
        self.limit = limit
        self.security["g"] = 2 # diffe-helman
        self.security["p"] = 2 # diffe-helman
        self.connections = {} # a dict of all current connections

    def __repr__(self):
        return "{}\n\nSecurity: {}\nCommands: {}\nQueues: {}\nWorkers: {}\nThreads: {} - {}\nConnections: {}\n\n{}".format(
        self.__str__(),
        self.security,
        self.commands,
        {k : self.queues[k].qsize() for k in self.queues},
        # threading.active_count(),
        self.workers,
        sum((len([True for i in self.threads[k] if i.is_alive()]) if type(self.threads[k]) == list else int(self.threads[k].is_alive()) for k in self.threads if k != "workers")),
        {k : ["{}-{}".format(i.name, int(i.is_alive())) for i in self.threads[k]] if type(self.threads[k]) == list else "{}-{}".format(self.threads[k].name, int(self.threads[k].is_alive())) for k in self.threads if k != "workers"},
        len(self.connections),
        "\n".join((repr(self.connections[i]) for i in self.connections))
        )
    def __str__(self):
        return "[{}:{}] {} -> {}/{}".format(
        self.addr if self.addr else "*.*.*.*",
        self.port,
        self.id,
        len(self.connections),
        self.limit
        )

    def open(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.addr, self.port))
            self.socket.listen(self.limit)
        except (ConnectionRefusedError, OSError) as e:
            return self.close(e)
        self.id = 1
        super().open()

    def close(self, err=CloseError(), end=True):
        super().close(err)
        if end:
            for id in [i for i in self.connections]:
                self.connections[id].close()

    @con_err
    def _worker_recv_loop(self):
        while self.id != -1:
            c_socket, addr = self.socket.accept()
            self.queues["received"].put((c_socket, addr))

    def _worker_handle(self):
        while self.id != -1:
            try:
                data = self.queues["received"].get(timeout=1)
                if data:
                    SClient(*data, self, {k[2:] : self.workers[k] for k in self.workers if k[:2] == "c_"})
                self.queues["received"].task_done()
            except queue.Empty: pass

    def _add_connection(self, client):
        self.connections[client.id] = client
    def _remove_connection(self, id):
        if id != -1:
            del self.connections[id]
