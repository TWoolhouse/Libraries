from engine.enums.mouse import Mouse
from vector import Vector

_mouse = { # Hashmap of all mouse codes to current status
    **{mouse.value: False for mouse in Mouse},
    Mouse.POS.value: Vector(0, 0)
}

def mouse(mouse: Mouse) -> bool:
    if isinstance(mouse, Mouse):
        mouse = mouse.value
    return _mouse[mouse]