__all__ = ["CloseError", "RemoteError", "DispatchError"]

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
    def __init__(self, node, cls, msg="Failed to Handle Request"):
        self.cls = cls
        self.msg = msg

    def __str__(self):
        return "'{}' -> {}".format(self.cls, self.msg)

def log(func):
    """Append Error to Node Error Queue and Re-Raise Error"""
    def log_error(node, *args, **kwargs):
        try:
            return func(node, *args, **kwargs)
        except Exception as e:
            node.err(e)
            raise
    return log_error

def handle(err: Exception, code: NodeBaseError=None, logging=True, close=False):
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
        return log(handle_error) if logging else handle_error
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
            func(dispatcher)
        except Exception as e:
            msg = "'{}': {}".format(type(e), e)
            raise DispatchError(dispatcher.node, dispatcher.__class__, msg).with_traceback(e.__traceback__) from None
    return dispatcher
