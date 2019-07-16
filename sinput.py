import time
import ctypes
import keys

# Import the SendInput object
SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)

class _KeyboardInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class _HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort)
    ]

class _MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class InputI(ctypes.Union):
    _fields_ = [
        ("ki", _KeyboardInput),
        ("mi", _MouseInput),
        ("hi", _HardwareInput)
    ]

class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", InputI)
    ]

def _send(func):
    def _send(type, *args, **kwargs):
        ii = InputI()
        func(ii, *args, **kwargs)
        x = Input(ctypes.c_ulong(type), ii)
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    return _send

@_send
def key_pressed(ii, code):
    ii.ki = _KeyboardInput(code, 0x48, 0, 0, ctypes.pointer(ctypes.c_ulong(0)))

@_send
def key_released(ii, code):
    ii.ki = _KeyboardInput(code, 0x48, 0x0002, 0, ctypes.pointer(ctypes.c_ulong(0)))

@_send
def mouse_pressed(ii, code=keys.LBUTTON):
    data = 0
    if code == keys.LBUTTON:
        flag = 0x0002
    elif code == keys.RBUTTON:
        flag = 0x0008
    elif code == keys.MBUTTON:
        flag = 0x0020
    elif code == keys.XBUTTON1:
        flag = 0x0080
        data = 0x0001
    elif code == keys.XBUTTON2:
        flag = 0x0080
        data = 0x0002
    else:
        flag = 0
    ii.mi = _MouseInput(0, 0, data, flag, 0, ctypes.pointer(ctypes.c_ulong(0)))

@_send
def mouse_released(ii, code=keys.LBUTTON):
    data = 0
    if code == keys.LBUTTON:
        flag = 0x0004
    elif code == keys.RBUTTON:
        flag = 0x0010
    elif code == keys.MBUTTON:
        flag = 0x0040
    elif code == keys.XBUTTON1:
        flag = 0x0100
        data = 0x0001
    elif code == keys.XBUTTON2:
        flag = 0x0100
        data = 0x0002
    else:
        flag = 0
    ii.mi = _MouseInput(0, 0, data, flag, 0, ctypes.pointer(ctypes.c_ulong(0)))

@_send
def mouse_moved(ii, x, y, rel):
    ii.mi = _MouseInput(x, y, 0, 0x0001 if rel else 0xC001, 0, ctypes.pointer(ctypes.c_ulong(0)))

def key_press(code):
    key_pressed(1, code)
def key_release(code):
    key_released(1, code)

def click(code, length=0):
    mouse_pressed(0, code)
    time.sleep(length)
    mouse_released(0, code)

def move(x, y, rel=True):
    mouse_moved(0, x, y, rel)

def key(code, length=0):
    key_press(code)
    time.sleep(length)
    key_release(code)
