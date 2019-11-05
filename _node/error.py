import queue

__all__ = ["CloseError", "RemoteError"]

class NodeBaseError(Exception):

    @classmethod
    def _sub_init(cls, func):
        def sub_init(self, *args, **kwargs):
            cls.__init__(self, args[0])
            func(self, *args, **kwargs)
        return sub_init

    @classmethod
    def _sub_str(cls, func):
        def sub_str(self):
            return cls.__str__(self)+" -> "+func(self)
        return sub_str

    def __init__(self, node):
        self.node = node

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__init__ = NodeBaseError._sub_init(cls.__init__)
        cls.__str__ = NodeBaseError._sub_str(cls.__str__)

    def __str__(self):
        return "{}: <{}>".format(self.__class__.__name__, self.node)

class CloseError(NodeBaseError):
    def __init__(self, node, msg="Connection Closed"):
        self.msg = msg

    def __str__(self):
        return "{}".format(self.msg)

class RemoteError(NodeBaseError):
    def __init__(self, node, msg):
        self.msg = msg

    def __str__(self):
        return "{}".format(self.msg)

class DispatchError(NodeBaseError):
    def __init__(self, node, cls):
        self.cls = cls

    def __str__(self):
        return "'{}' is not a Valid Dispatcher".format(self.cls)

def close_err(func):
    def close_error(node, *args, **kwargs):
        try:
            return func(node, *args, **kwargs)
        except CloseError as e:
            return e
    return close_error

def con_err(func):
    """Close Node on Network Errors"""
    def connection_error(node, *args, **kwargs):
        try:
            return func(node, *args, **kwargs)
        except (ConnectionError, OSError) as e:
            node.close()
            raise CloseError(node) from e
    return connection_error

def log_err(func):
    """Append Error to Node Error Queue and Re-Raise Error"""
    def log_error(node, *args, **kwargs):
        try:
            return func(node, *args, **kwargs)
        except Exception as e:
            node.err(e)
            raise
    return log_error

def que_err(func):
    def queue_error(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except queue.Empty:
            pass
    return queue_error

def con_active(func):
    """Call Func if Node is Active"""
    def connection_active(node, *args, **kwargs):
        if node:
            return func(node, *args, **kwargs)
        raise CloseError(node)
    return connection_active
