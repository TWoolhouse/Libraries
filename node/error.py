__all__ = ["CloseError", "RemoteError", "DispatchError"]

class MetaNodeError(type):

    node = "NODE"

    def __new__(cls, name, bases, dct):
        if "__str__" in dct:
            def new_str(func):
                def _str_(self):
                    return "{}: <{}".format(self.__class__.__name__, self.node) + " -> " + func(self) + ">"
                return _str_
            dct["__str__"] = new_str(dct["__str__"])
        return super().__new__(cls, name, bases, dct)

    def __call__(cls, node, *args, **kwargs):
        self = super().__call__(*args, **kwargs)
        self.node = node
        return self

class NodeBaseError(Exception, metaclass=MetaNodeError):

    def __repr__(self) -> str:
        return self.__str__()

class NodeError(NodeBaseError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self) -> str:
        return self.msg.__str__()

class CloseError(NodeError):
    def __init__(self, msg="Connection Closed"):
        super().__init__(msg)

class RemoteError(NodeError):
    pass
class EncryptionError(NodeError):
    pass

class DispatchError(NodeBaseError):
    def __init__(self, cls, msg="Failed to Handle Request"):
        self.cls = cls
        self.msg = msg

    def __str__(self):
        return "'{}' -> {}".format(self.cls.__name__, self.msg)

def log(func):
    """Append Error to Node Error Queue and Re-Raise Error"""
    def log_error(node, *args, **kwargs):
        try:
            return func(node, *args, **kwargs)
        except Exception as e:
            print("ERROR:", e)
            node.err(e)
            raise
    return log_error

def handle(err: Exception, code: NodeBaseError=None, close=False):
    def handle_error(func):
        def handle_error(node, *args, **kwargs):
            try:
                return func(node, *args, **kwargs)
            except err as e:
                if code is True:
                    raise e
                elif isinstance(code, Exception):
                    raise code(node) from e
                if close:
                    node.close()
        return handle_error
    return handle_error

def con_active(func):
    """Call Func if Node is Active"""
    def connection_active(node, *args, **kwargs):
        if node:
            return func(node, *args, **kwargs)
        raise CloseError(node)
    return connection_active

def dispatch(func):
    def dispatcher(dispatcher):
        try:
            return func(dispatcher)
        except Exception as e:
            msg = "{}".format("" if isinstance(e, NodeBaseError) else e.__class__.__name__) + "{}".format(e)
            # msg = "'{}': {}".format(e.__class__.__name__, e)
            raise DispatchError(dispatcher.node, dispatcher.__class__, msg).with_traceback(e.__traceback__) from None
    return dispatcher
