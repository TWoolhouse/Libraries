from .log import create as _create, page

server = _create("server", "[{asctime}] {levelname} {message}")
request = _create("request", "[{asctime}]<{_addr}:{_port}@{_ssl}> {message}")
