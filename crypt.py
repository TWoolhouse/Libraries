def encrypt_bytes(message: bytes, key: bytes):

    key *= len(message) // len(key) + 1
    return bytes((m ^ k for m,k in zip(message, key)))

decrypt_bytes = encrypt_bytes

def encrypt(message, key, decode=False):
    msg = encrypt_bytes(message if isinstance(message, bytes) else str(message).encode("utf-8"), key if isinstance(key, bytes) else str(key).encode("utf-8"))
    return msg.decode("utf-8") if decode else msg

def decrypt(message, key, decode=True):
    return encrypt(message, key, decode)
