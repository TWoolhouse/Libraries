def encrypt_bytes(message: bytes, key: bytes):

    key *= len(message) // len(key) + 1
    return bytes((m ^ k for m,k in zip(message, key)))

decrypt_bytes = encrypt_bytes

def encrypt(message, key):
    if isinstance(message, bytes):    pass
    elif isinstance(message, int):
        message = ibytes(message)
    else:
        message = str(message).encode("utf-8")

    if isinstance(key, bytes):    pass
    elif isinstance(key, int):
        key = ibytes(key)
    else:
        key = str(key).encode("utf-8")
    return encrypt_bytes(message, key)

def decrypt(message, key, decode=False):
    msg = encrypt(message, key)
    if decode:
        return msg.decode("utf-8")
    return msg

def ibytes(value: int) -> bytes:
    return value.to_bytes(value.bit_length() // 8 + 1, byteorder="big")
