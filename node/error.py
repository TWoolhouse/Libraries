import traceback

__all__ = ["CloseError", "RemoteError", "DispatchError"]

def _exception_info(exception: Exception):
    frame = traceback.extract_tb(exception.__traceback__)[-1]
    return (exception.__class__.__name__, str(exception), frame.lineno, frame.name)

class NodeBaseError(Exception):

    def __init__(self, node):
        self.node = node

    def __repr__(self) -> str:
        return self.__str__()

class NodeError(NodeBaseError):
    def __init__(self, node, msg):
        super().__init__(node)
        self.msg = msg

    def __str__(self) -> str:
        return self.msg.__str__()

class CloseError(NodeError):
    def __init__(self, node, msg="Connection Closed"):
        super().__init__(node, msg)

class RemoteError(NodeError):
    pass
class EncryptionError(NodeError):
    pass

class DispatchError(NodeBaseError):
    def __init__(self, node, cls, msg="Failed to Handle Request"):
        super().__init__(node)
        self.cls = cls
        self.msg = msg

    def __str__(self):
        return "{} {}".format(self.cls.__name__, self.msg)

def log(*exceptions: Exception, output=True, tb=True):
    def log_func(func):
        """Append Error to Node Error Queue and Re-Raise Error"""
        def log_error(node, *args, **kwargs):
            try:
                return func(node, *args, **kwargs)
            except Exception as e:
                if output and not any(isinstance(e, i) for i in exceptions):
                    trace = _exception_info(e)
                    print("{} {}: {}".format(node, e.__class__.__name__, e))
                node.err(e)
                raise
        return log_error
    return log_func

def handle(err: Exception, code: NodeBaseError=None, close=False):
    def handle_error(func):
        def handle_error(node, *args, **kwargs):
            try:
                return func(node, *args, **kwargs)
            except err as e:
                if close:
                    node.close()
                if code is True:
                    raise e
                elif issubclass(code, Exception):
                    raise code(node) from e
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
            msg = "{}: {}".format("" if isinstance(e, NodeBaseError) else e.__class__.__name__, e)
            raise DispatchError(dispatcher.node, dispatcher.__class__, msg).with_traceback(e.__traceback__) from None
    return dispatcher
