from ..enums.keys import Key

_keys = { # Hashmap of all key codes to current status
    key.value: False  for key in Key
}

def key(key: Key) -> bool:
    if isinstance(key, Key):
        key = key.value
    return _keys[key]