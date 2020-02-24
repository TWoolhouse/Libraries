from engine.enums.keys import Key

_keys = { # Hashmap of all key codes to current status
    65: False, # A
    68: False, # D
    87: False, # W
    83: False, # S
    69: False, # E
    81: False, # Q
    82: False, # R
    70: False, # F
}

def key(key: Key) -> bool:
    if isinstance(key, Key):
        key = key.value
    return _keys[key]