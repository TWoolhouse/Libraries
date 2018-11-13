def hash(text, start_val=47694282734):
    total = hex(start_val + sum([int("".join([str(ord(x)) for x in text[i:]])) for i in range(0, len(text))]))[2:]
    while len(total) > 8:
        total = hex(sum([int((total*2)[i:i+8], 16) for i in range(0, len(total), 4)]))[2:]
    return total

print(hash("Hello World!"))
