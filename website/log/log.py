import logging
import os.path
from path import PATH
from ..config import config
from collections import namedtuple

if not os.path.isdir(dirname := f"{PATH}log"):
    os.makedirs(dirname)

formatter = logging.Formatter(
    "[{asctime}]<{_addr}:{_port}@{_ssl}> {module}.{funcName} -> {message}",
    datefmt="%Y/%m/%d %H:%M:%S", style="{"
)

class ClientLogger(logging.Logger):

    def _clog(self, func, msg, client, *args, **kwargs):
        ex = kwargs.pop("extra", {})
        ex["client"] = client
        if er := kwargs.pop("exc_info", None):
            er = (er, er, er.__traceback__)
        return func(msg, *args, extra=ex, stacklevel=3, exc_info=er, **kwargs)

    def debug(self, msg, client, *args, **kwargs):
        return self._clog(super().debug, msg, client, *args, **kwargs)
    def info(self, msg, client, *args, **kwargs):
        return self._clog(super().info, msg, client, *args, **kwargs)
    def warning(self, msg, client, *args, **kwargs):
        return self._clog(super().warning, msg, client, *args, **kwargs)
    def error(self, msg, client, *args, **kwargs):
        return self._clog(super().error, msg, client, *args, **kwargs)
    def critical(self, msg, client, *args, **kwargs):
        return self._clog(super().critical, msg, client, *args, **kwargs)

class Handle(logging.FileHandler):

    def __init__(self, file: str, mode: str):
        self._trace_handle = logging.FileHandler(f"{PATH}log/{file}.trace.log", mode, "utf-8")
        self._trace_handle.setLevel(logging.NOTSET)
        self._trace_handle.setFormatter(formatter)
        super().__init__(f"{PATH}log/{file}.log", mode, "utf-8")

    def format(self, record):
        cli = record.__dict__["client"]
        if cli is None:
            record.__dict__["_addr"] = "0.0.0.0"
            record.__dict__["_port"] = "0"
            record.__dict__["_ssl"] = "O"
        else:
            record.__dict__["_addr"] = cli.peer
            record.__dict__["_port"] = cli.port
            record.__dict__["_ssl"] = "X" if cli.ssl else "O"
        err = record.exc_info
        record.exc_info = False
        msg = super().format(record)
        if err:
            record.exc_info = err
            self._trace_handle.emit(record)
        return msg

page_loggers = {}

def page(name: str, fmt: str=None) -> ClientLogger:
    return page_loggers.get(name, create(name, fmt))

def create(name: str, fmt: str=None) -> ClientLogger:
    logging.Logger.manager.setLoggerClass(ClientLogger)
    logger = logging.getLogger(f"website.{name}")
    logging.Logger.manager.setLoggerClass(logging.Logger)
    logger.setLevel(logging.DEBUG)
    handle = Handle(name, "a")
    if fmt:
        fmtr = logging.Formatter(fmt, datefmt="%Y/%m/%d %H:%M:%S", style="{")
        handle.setFormatter(fmtr)
        handle._trace_handle.setFormatter(fmtr)
    else:
        handle.setFormatter(formatter)
    logger.addHandler(handle)
    page_loggers[name] = logger
    return logger

create("default")
