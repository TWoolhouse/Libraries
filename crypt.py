def encrypt_bytes(message, key):
    output = []

    for c in message:
        for k in key:
            c = c ^ k
        output.append(c)

    return bytes(output)

def decrypt_bytes(message, key):
    return encrypt_bytes(message, key[::-1])

def encrypt(message, key, decode=True):
    msg = encrypt_bytes(message if type(message) == bytes else message.encode("utf-8"), key if type(key) == bytes else key.encode("utf-8"))
    return msg.decode("utf-8") if decode else msg

def decrypt(message, key, decode=True):
    return encrypt(message, key[::-1], decode)
