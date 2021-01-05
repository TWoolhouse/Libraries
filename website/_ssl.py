import ssl

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
try:
    context.load_cert_chain("C:/dev/Code/Webpage/SSL/dino_ssl.crt", "C:/dev/Code/Webpage/SSL/dino_ssl.key")
except FileNotFoundError:
    # context.load_default_certs(ssl.Purpose.CLIENT_AUTH)
    pass