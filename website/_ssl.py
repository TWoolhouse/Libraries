import ssl
from .config import config

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
try:
    cfg = config("server.cfg")["server"]
    context.load_cert_chain(f"{cfg['ssl_key']}.crt", f"{cfg['ssl_key']}.key")
except FileNotFoundError:
    try:
        context.load_default_certs(ssl.Purpose.CLIENT_AUTH)
    except Exception:
        pass
