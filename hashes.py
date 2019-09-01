import hashlib

def byte(arg):
    return arg if type(arg) == bytes else str(arg).encode("utf-8")

def new(name="sha256", *data):
    h = hashlib.new(name)
    for d in data:
        h.update(byte(d))
    return h.digest()

def hmac(message, salt, name="sha256", iterations=100000):
    return hashlib.pbkdf2_hmac(name, byte(message), byte(salt)*(32//len(str(salt))+1), iterations)
