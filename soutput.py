import msvcrt
import keys

def kbfunc():
    if msvcrt.kbhit():
        return msvcrt.getch()
    return False

def get_key(decode=True):
    char = kbfunc()
    if char:
        if decode:
            try:
                char = char.decode()
            except UnicodeDecodeError:  return False
        return char

def poll(char):
    return get_key(type(char) != bytes) == char
